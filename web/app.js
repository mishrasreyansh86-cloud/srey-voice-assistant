const STARS_COUNT = 900;
const WAKE_WORDS = [
    "hey srey", "hey sri", "hey shree", "hey sray", "hey shrey",
    "hey sir", "hey trey", "history", "hey straight", "hey ray"
];
const COMMAND_DEBOUNCE_MS = 1200;
const FOLLOWUP_MS = 12000;
const COMMAND_HINT = /^(play |google |search |look up |remember |take a note|take note|volume |mute|screenshot|read my notes|show my notes|open |launch |weather |what time|whats the time|what's the time|what is the time|what is the date)/;
const STATE = {
    IDLE: "IDLE",
    LISTENING: "LISTENING...",
    THINKING: "THINKING...",
    SPEAKING: "SPEAKING..."
};

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false, powerPreference: "high-performance" });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.25));
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);
renderer.domElement.style.filter = "drop-shadow(0 0 18px rgba(255, 255, 255, 0.55))";
renderer.domElement.style.transition = "filter 0.25s ease";

const starGeometry = new THREE.BufferGeometry();
const starPositions = new Float32Array(STARS_COUNT * 3);
for (let i = 0; i < STARS_COUNT * 3; i += 3) {
    starPositions[i] = (Math.random() - 0.5) * 45;
    starPositions[i + 1] = (Math.random() - 0.5) * 45;
    starPositions[i + 2] = (Math.random() - 0.5) * 45;
}
starGeometry.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
const starMaterial = new THREE.PointsMaterial({ size: 0.05, color: 0xe6edf3, transparent: true, opacity: 0.7 });
const starField = new THREE.Points(starGeometry, starMaterial);
scene.add(starField);

const matRing = new THREE.MeshBasicMaterial({ color: 0xE6EDF3, wireframe: true });
const ring1 = new THREE.Mesh(new THREE.TorusGeometry(1.2, 0.05, 8, 48), matRing);
const ring2 = new THREE.Mesh(new THREE.TorusGeometry(0.9, 0.05, 8, 48), matRing);
const ring3 = new THREE.Mesh(new THREE.TorusGeometry(0.6, 0.05, 8, 48), matRing);
const coreGeo = new THREE.IcosahedronGeometry(0.32, 1);
const coreMat = new THREE.MeshBasicMaterial({ color: 0x7af0ff, wireframe: true, transparent: true, opacity: 0.95 });
const coreMesh = new THREE.Mesh(coreGeo, coreMat);
const ring4 = new THREE.Mesh(new THREE.TorusGeometry(1.55, 0.015, 6, 64), matRing);
ring1.rotation.x = Math.PI / 2;
ring2.rotation.y = Math.PI / 4;
ring3.rotation.z = Math.PI / 3;
ring4.rotation.x = Math.PI / 3;
ring1.position.y = ring2.position.y = ring3.position.y = ring4.position.y = coreMesh.position.y = 0.4;
scene.add(ring1, ring2, ring3, ring4, coreMesh);
camera.position.z = 6.5;

const statusTag = document.getElementById("status-tag");
const caption = document.getElementById("live-caption");
const hudTime = document.getElementById("hud-time");
const hudDate = document.getElementById("hud-date");
const hudCpu = document.getElementById("hud-cpu");
const hudRam = document.getElementById("hud-ram");
const cpuFill = document.getElementById("cpu-fill");
const ramFill = document.getElementById("ram-fill");
const hudNeural = document.getElementById("hud-neural");
const neuralFill = document.getElementById("neural-fill");
const hexDump = document.getElementById("hex-dump");
const hudPing = document.getElementById("hud-ping");
const sigState = document.getElementById("sig-state");
const coordLine = document.getElementById("coord-line");
const canvas = document.getElementById("waveform-canvas");
const ctx = canvas.getContext("2d", { alpha: true });

let rotSpeed = 0.003;
let starSpeed = 0.0006;
let currentState = STATE.IDLE;
let audioContext, analyser, dataArray, isAudioInitialized = false;
let recognition = null;
let isAwake = false;
let commandTimer = null;
let pendingCommand = "";
let commandSent = false;
let listenWatchdog = null;
let submitWatchdog = null;
let typeTimeout = null;
let animFrame = 0;
let pageVisible = true;

let pointerX = 0;
let pointerY = 0;
let hexLines = [];

function setMode(mode) {
    document.body.dataset.mode = mode;
    if (hudNeural) hudNeural.innerText = mode.toUpperCase();
    if (neuralFill) {
        const widths = { idle: "12%", listening: "78%", thinking: "94%", speaking: "62%" };
        neuralFill.style.width = widths[mode] || "12%";
    }
    if (sigState) sigState.innerText = mode === "idle" ? "PASSIVE" : "LOCKED";
}

function setGlow(filterValue) {
    renderer.domElement.style.filter = filterValue;
}

function tickHexDump() {
    if (!hexDump) return;
    const chunk = Array.from({ length: 6 }, () => Math.floor(Math.random() * 256).toString(16).padStart(2, "0")).join(" ").toUpperCase();
    hexLines.unshift(`${Date.now().toString(16).slice(-6).toUpperCase()}  ${chunk}`);
    hexLines = hexLines.slice(0, 9);
    hexDump.textContent = hexLines.join("\n");
}

async function initAudioVisualizer() {
    if (isAudioInitialized) return;
    try {
        const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 32;
        analyser.smoothingTimeConstant = 0.7;
        audioContext.createMediaStreamSource(micStream).connect(analyser);
        dataArray = new Uint8Array(analyser.frequencyBinCount);
        isAudioInitialized = true;
    } catch (err) {}
}

function stripWakeWords(text) {
    let clean = text;
    for (let i = 0; i < WAKE_WORDS.length; i++) {
        clean = clean.split(WAKE_WORDS[i]).join("");
    }
    return clean.replace(/[^a-zA-Z0-9 ]/g, "").trim();
}

function containsWakeWord(text) {
    for (let i = 0; i < WAKE_WORDS.length; i++) {
        if (text.includes(WAKE_WORDS[i])) return true;
    }
    return false;
}

function looksLikeCommand(text) {
    return COMMAND_HINT.test(stripWakeWords(text));
}

function mergeCommand(previous, next) {
    if (!next) return previous;
    if (!previous) return next;
    if (next.startsWith(previous) || next.includes(previous)) return next;
    if (previous.includes(next)) return previous;
    return (previous + " " + next).replace(/\s+/g, " ").trim();
}

function canListen() {
    return pageVisible && currentState !== STATE.SPEAKING && currentState !== STATE.THINKING;
}

function clearTimers() {
    if (commandTimer) {
        clearTimeout(commandTimer);
        commandTimer = null;
    }
    if (listenWatchdog) {
        clearTimeout(listenWatchdog);
        listenWatchdog = null;
    }
    if (submitWatchdog) {
        clearTimeout(submitWatchdog);
        submitWatchdog = null;
    }
}

function armFollowupStandby() {
    if (listenWatchdog) clearTimeout(listenWatchdog);
    listenWatchdog = setTimeout(() => {
        if (commandSent || currentState !== STATE.LISTENING) return;
        if (pendingCommand && pendingCommand.length > 2) {
            submitCommand(pendingCommand);
            return;
        }
        set_ai_state(STATE.IDLE);
    }, FOLLOWUP_MS);
}

function submitCommand(command) {
    command = (command || pendingCommand || "").trim();
    if (commandSent || command.length < 3) return;
    if (currentState === STATE.SPEAKING || currentState === STATE.THINKING) return;

    commandSent = true;
    pendingCommand = "";
    clearTimers();
    caption.innerText = `[YOU] ❯ ${command}`;
    eel.handle_user_speech(command)();

    submitWatchdog = setTimeout(() => {
        if (commandSent && currentState === STATE.LISTENING) {
            commandSent = false;
            isAwake = true;
        }
    }, 1500);
}

function queueCommand(command) {
    if (!command || command.length < 3) return;
    pendingCommand = mergeCommand(pendingCommand, command);
    caption.innerText = `[YOU] ❯ ${pendingCommand}`;
    if (commandTimer) clearTimeout(commandTimer);
    commandTimer = setTimeout(() => submitCommand(pendingCommand), COMMAND_DEBOUNCE_MS);
    armFollowupStandby();
}

function wakeUp() {
    isAwake = true;
    commandSent = false;
    if (currentState !== STATE.LISTENING) set_ai_state(STATE.LISTENING);
    armFollowupStandby();
}

function safeStart() {
    if (!recognition || !canListen()) return;
    try {
        recognition.start();
    } catch (e) {}
}

function drawWaveform() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!isAudioInitialized || !dataArray) {
        ctx.strokeStyle = "rgba(122, 240, 255, 0.45)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        const time = performance.now() * 0.003;
        const mid = canvas.height / 2;
        for (let x = 0; x < canvas.width; x += 4) {
            const y = mid + Math.sin(x * 0.03 + time) * 3;
            if (x === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();
        return;
    }

    analyser.getByteFrequencyData(dataArray);
    const barWidth = (canvas.width / dataArray.length) * 1.5;
    let x = 0;
    ctx.fillStyle = "#7af0ff";
    for (let i = 0; i < dataArray.length; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;
        ctx.fillRect(x, canvas.height - barHeight, barWidth - 2, barHeight);
        x += barWidth + 1;
    }
}

function animate() {
    requestAnimationFrame(animate);
    if (!pageVisible) return;

    animFrame++;
    starField.rotation.y += starSpeed;
    ring1.rotation.x += rotSpeed;
    ring1.rotation.y += rotSpeed * 0.5;
    ring2.rotation.y += rotSpeed * 1.5;
    ring2.rotation.z += rotSpeed * 0.8;
    ring3.rotation.z += rotSpeed * 2.0;
    ring3.rotation.x += rotSpeed * 1.2;

    if (currentState === STATE.LISTENING && isAudioInitialized) {
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
        const targetScale = Math.min(1.8, 1.0 + ((sum / dataArray.length) / 70.0));
        ring1.scale.setScalar(ring1.scale.x + (targetScale - ring1.scale.x) * 0.2);
        ring2.scale.setScalar(ring2.scale.x + (targetScale - ring2.scale.x) * 0.2);
        ring3.scale.setScalar(ring3.scale.x + (targetScale - ring3.scale.x) * 0.2);
    } else if (animFrame % 2 === 0) {
        const next = ring1.scale.x + (1.0 - ring1.scale.x) * 0.1;
        ring1.scale.setScalar(next);
        ring2.scale.setScalar(next);
        ring3.scale.setScalar(next);
    }

    coreMesh.rotation.y += rotSpeed * 1.8;
    coreMesh.rotation.x += rotSpeed * 0.9;
    ring4.rotation.z += rotSpeed * 0.35;
    camera.position.x += (pointerX * 0.35 - camera.position.x) * 0.04;
    camera.position.y += (-pointerY * 0.2 + 0.15 - camera.position.y) * 0.04;
    camera.lookAt(0, 0.4, 0);
    if (coordLine && animFrame % 8 === 0) {
        coordLine.innerText = `X ${camera.position.x.toFixed(3)}  Y ${camera.position.y.toFixed(3)}  Z ${camera.position.z.toFixed(3)}`;
    }
    renderer.render(scene, camera);
    if (animFrame % 2 === 0) drawWaveform();
}

function updateClock() {
    const now = new Date();
    hudTime.innerText = now.toLocaleTimeString("en-US", { hour12: false });
    hudDate.innerText = now.toLocaleDateString("en-US", {
        weekday: "short", month: "short", day: "2-digit"
    }).toUpperCase();
    if (hudPing) hudPing.innerText = String(8 + (now.getSeconds() % 17));
}

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.lang = "en-IN";

    recognition.onresult = (event) => {
        if (!canListen() || commandSent) return;

        let transcript = "";
        for (let i = 0; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }

        const lower = transcript.toLowerCase().trim();
        if (!lower) return;

        if (!isAwake && (containsWakeWord(lower) || looksLikeCommand(lower))) {
            wakeUp();
        }

        if (!isAwake) {
            caption.innerText = `[HEARING...] ❯ ${lower}`;
            return;
        }

        const cleanCommand = stripWakeWords(lower);
        if (cleanCommand.length > 2) queueCommand(cleanCommand);
        else armFollowupStandby();
    };

    recognition.onerror = (event) => {
        if (event.error === "aborted") return;
        setTimeout(safeStart, 50);
    };

    recognition.onend = () => {
        if (canListen()) setTimeout(safeStart, 40);
    };
}

window.addEventListener("load", () => {
    initAudioVisualizer();
    safeStart();
});
window.addEventListener("click", () => {
    initAudioVisualizer();
    safeStart();
});
document.addEventListener("visibilitychange", () => {
    pageVisible = document.visibilityState === "visible";
    if (pageVisible) safeStart();
});

animate();
setInterval(updateClock, 1000);
setInterval(tickHexDump, 180);
tickHexDump();
updateClock();
setMode("idle");

window.addEventListener("mousemove", (event) => {
    pointerX = (event.clientX / window.innerWidth) * 2 - 1;
    pointerY = (event.clientY / window.innerHeight) * 2 - 1;
});

eel.expose(update_telemetry);
function update_telemetry(cpu, ram) {
    hudCpu.innerText = cpu + "%";
    cpuFill.style.width = cpu + "%";
    hudRam.innerText = ram + "%";
    ramFill.style.width = ram + "%";
}

eel.expose(set_ai_state);
function set_ai_state(state) {
    clearTimeout(typeTimeout);
    currentState = state;

    if (state === STATE.LISTENING) {
        isAwake = true;
        commandSent = false;
        armFollowupStandby();
        setMode("listening");
        setGlow("drop-shadow(0 0 32px rgba(90, 255, 230, 0.95))");
        rotSpeed = 0.05;
        starSpeed = 0.003;
        statusTag.innerText = "CORE // LISTENING...";
        if (!caption.innerText.includes("[YOU]")) caption.innerText = "[SYS] Listening for command...";
        setTimeout(safeStart, 80);
    } else if (state === STATE.THINKING) {
        if (listenWatchdog) {
            clearTimeout(listenWatchdog);
            listenWatchdog = null;
        }
        setMode("thinking");
        setGlow("drop-shadow(0 0 28px rgba(255, 204, 102, 0.85))");
        rotSpeed = 0.02;
        starSpeed = 0.0015;
        statusTag.innerText = "CORE // PROCESSING...";
        if (recognition) {
            try { recognition.stop(); } catch (e) {}
        }
    } else if (state === STATE.SPEAKING) {
        setMode("speaking");
        setGlow("drop-shadow(0 0 34px rgba(255, 255, 255, 1.0))");
        rotSpeed = 0.015;
        starSpeed = 0.001;
        statusTag.innerText = "CORE // RESPONDING...";
        if (recognition) {
            try { recognition.stop(); } catch (e) {}
        }
    } else {
        isAwake = false;
        commandSent = false;
        pendingCommand = "";
        clearTimers();
        setMode("idle");
        setGlow("drop-shadow(0 0 20px rgba(122, 240, 255, 0.7))");
        rotSpeed = 0.003;
        starSpeed = 0.0006;
        statusTag.innerText = 'STANDBY // SAY "HEY SREY"';
        caption.innerText = "[SYS] Waiting for wake word: HEY SREY";
        setTimeout(safeStart, 80);
    }
}

eel.expose(display_ai_response);
function display_ai_response(text) {
    if (!caption) return;
    clearTimeout(typeTimeout);
    caption.textContent = `[SREY] ❯ ${text}`;
}

window.addEventListener("resize", () => {
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
});
