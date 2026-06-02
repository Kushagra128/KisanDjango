(function () {
	"use strict";

	// ── Prevent double-init ───────────────────────────────────────────────────
	if (window.__kisanWidgetLoaded) return;
	window.__kisanWidgetLoaded = true;

	// ── Read config from the <script> tag that loaded this file ──────────────
	// Usage: <script src="kisan-widget.js" data-api="https://yourdomain.com"></script>
	var scriptTag =
		document.currentScript ||
		(function () {
			var scripts = document.getElementsByTagName("script");
			return scripts[scripts.length - 1];
		})();

	var API_BASE = (scriptTag.getAttribute("data-api") || "").replace(/\/$/, "");
	if (!API_BASE) {
		// Auto-detect: same origin as the script src
		try {
			var src = scriptTag.src;
			var url = new URL(src);
			API_BASE = url.origin;
		} catch (e) {
			API_BASE = "http://localhost:8000";
		}
	}

	var POSITION = scriptTag.getAttribute("data-position") || "bottom-right";

	// Position mapping
	var posMap = {
		"bottom-right": {
			bottom: "24px",
			right: "24px",
			left: "auto",
			top: "auto",
		},
		"bottom-left": { bottom: "24px", left: "24px", right: "auto", top: "auto" },
	};
	var pos = posMap[POSITION] || posMap["bottom-right"];

	// ── CSS (all scoped inside shadow DOM) ───────────────────────────────────
	var CSS = `
    *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }

    :host { all: initial; font-family: "Segoe UI","Noto Sans Devanagari",system-ui,-apple-system,sans-serif; }

    /* ── Scrollbar ── */
    .scroll::-webkit-scrollbar { width: 4px; }
    .scroll::-webkit-scrollbar-thumb { background:#f59e0b; border-radius:99px; }
    .scroll::-webkit-scrollbar-track { background:transparent; }

    /* ── Animations ── */
    @keyframes float  { 0%,100%{transform:translateY(0)}  50%{transform:translateY(-7px)} }
    @keyframes bounce { 0%,100%{transform:translateY(0)}  50%{transform:translateY(-5px)} }
    @keyframes pulse  { 0%,100%{opacity:1}                50%{opacity:0.4}                }
    @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
    @keyframes spin   { to{transform:rotate(360deg)} }

    .float  { animation: float  3s ease-in-out infinite; }
    .dot1   { animation: bounce 1s ease-in-out 0s    infinite; }
    .dot2   { animation: bounce 1s ease-in-out 0.15s infinite; }
    .dot3   { animation: bounce 1s ease-in-out 0.3s  infinite; }
    .pulse  { animation: pulse  2s ease-in-out infinite; }
    .fade-in{ animation: fadeIn 0.25s ease-out; }

    /* ── Toggle button ── */
    #toggleBtn {
      position:fixed;
      bottom:${pos.bottom}; right:${pos.right}; left:${pos.left}; top:${pos.top};
      z-index:2147483647;
      width:62px; height:62px; border-radius:50%;
      background:linear-gradient(135deg,#f59e0b,#ea580c);
      color:#fff; font-size:28px;
      border:3px solid rgba(255,255,255,0.7);
      cursor:pointer;
      box-shadow:0 8px 28px rgba(234,88,12,0.5);
      display:flex; align-items:center; justify-content:center;
      transition:transform .2s,box-shadow .2s;
    }
    #toggleBtn:hover { transform:scale(1.1); box-shadow:0 12px 32px rgba(234,88,12,0.6); }
    #toggleBtn.hidden { display:none; }

    /* ── Widget panel ── */
    #widget {
      position:fixed;
      bottom:100px; right:${pos.right}; left:${pos.left};
      z-index:2147483646;
      width:430px; max-width:96vw;
      height:690px; max-height:88vh;
      border-radius:28px;
      background:rgba(255,255,255,0.96);
      backdrop-filter:blur(24px);
      border:1px solid rgba(255,255,255,0.8);
      box-shadow:0 24px 60px rgba(0,0,0,0.18),0 8px 24px rgba(251,191,36,0.15);
      display:none; flex-direction:column; overflow:hidden;
    }
    #widget.open { display:flex; }

    /* ── Header ── */
    .hdr {
      background:linear-gradient(100deg,#f97316,#f59e0b 60%,#eab308);
      padding:15px 18px; color:#fff;
      display:flex; align-items:center; justify-content:space-between;
      flex-shrink:0;
    }
    .hdr-left { display:flex; align-items:center; gap:11px; }
    .hdr-avatar {
      width:46px; height:46px; border-radius:50%;
      background:rgba(255,255,255,0.25);
      display:flex; align-items:center; justify-content:center;
      font-size:22px; flex-shrink:0;
    }
    .hdr h2 { font-size:17px; font-weight:700; letter-spacing:0.3px; }
    .hdr-status { display:flex; align-items:center; gap:5px; font-size:11.5px; opacity:0.9; margin-top:2px; }
    .hdr-dot { width:7px; height:7px; border-radius:50%; background:#86efac; }
    #closeBtn {
      width:32px; height:32px; border-radius:50%;
      background:rgba(255,255,255,0.2); border:none;
      color:#fff; font-size:15px; cursor:pointer;
      display:flex; align-items:center; justify-content:center;
      transition:background .2s; flex-shrink:0;
    }
    #closeBtn:hover { background:rgba(255,255,255,0.35); }

    /* ── Chips ── */
    .chips {
      padding:9px 12px;
      background:rgba(255,255,255,0.97);
      border-bottom:1px solid #fde68a;
      display:flex; gap:7px; overflow-x:auto; flex-shrink:0;
    }
    .chips::-webkit-scrollbar { height:0; }
    .chip {
      padding:6px 13px; border-radius:99px;
      background:#fffbeb; border:1px solid #fcd34d;
      color:#92400e; font-size:12.5px; font-weight:500;
      white-space:nowrap; cursor:pointer;
      transition:all .18s; flex-shrink:0;
      font-family:inherit;
    }
    .chip:hover:not(:disabled) { background:#f59e0b; color:#fff; border-color:#f59e0b; }
    .chip:disabled { opacity:0.45; cursor:not-allowed; }

    /* ── Messages ── */
    #messages {
      flex:1; overflow-y:auto; padding:14px;
      display:flex; flex-direction:column; gap:12px;
      background:linear-gradient(180deg,#fffbeb55,#fff);
    }
    .msg-row { display:flex; gap:9px; align-items:flex-end; }
    .msg-row.user { flex-direction:row-reverse; }
    .msg-av {
      width:33px; height:33px; border-radius:50%;
      background:linear-gradient(135deg,#f59e0b,#ea580c);
      color:#fff; font-size:14px;
      display:flex; align-items:center; justify-content:center;
      flex-shrink:0;
    }
    .msg-row.user .msg-av { background:#374151; }
    .bubble {
      max-width:80%; padding:11px 15px;
      font-size:14px; line-height:1.75; border-radius:20px;
    }
    .bubble.bot {
      background:#fff; color:#1e293b;
      border-bottom-left-radius:4px;
      box-shadow:0 2px 10px rgba(0,0,0,0.07);
      border:1px solid rgba(251,191,36,0.25);
    }
    .bubble.user {
      background:linear-gradient(135deg,#f97316,#f59e0b);
      color:#fff; border-bottom-right-radius:4px;
      box-shadow:0 3px 10px rgba(249,115,22,0.3);
    }

    /* ── Typing indicator ── */
    #typing { padding:0 14px 8px; display:none; }
    #typing.show { display:block; }
    .typing-wrap { display:flex; gap:9px; align-items:flex-end; }
    .typing-dots {
      display:flex; gap:5px; align-items:center;
      background:#fff; padding:12px 16px;
      border-radius:20px; border-bottom-left-radius:4px;
      box-shadow:0 2px 10px rgba(0,0,0,0.07);
      border:1px solid rgba(251,191,36,0.2);
    }
    .typing-dots span {
      width:8px; height:8px; border-radius:50%;
      background:#f59e0b; display:inline-block;
    }

    /* ── Status bar ── */
    #statusBar {
      display:none; text-align:center; font-size:11.5px;
      color:#b45309; background:#fef3c7;
      padding:4px 10px; border-bottom:1px solid #fde68a;
      flex-shrink:0;
    }
    #statusBar.show { display:block; }

    /* ── Input area ── */
    .inp-area {
      padding:11px 13px 9px;
      background:rgba(255,255,255,0.98);
      border-top:1px solid #fde68a; flex-shrink:0;
    }
    .inp-row { display:flex; gap:7px; align-items:center; }
    .inp-area.busy #messageInput { opacity:0.55; cursor:not-allowed; }
    .inp-area.busy #sendBtn      { opacity:0.45; cursor:not-allowed; }
    .inp-area.busy #voiceBtn     { opacity:0.45; cursor:not-allowed; }

    #voiceBtn {
      width:42px; height:42px; border-radius:50%;
      background:#fef3c7; border:none; color:#b45309;
      font-size:16px; cursor:pointer;
      display:flex; align-items:center; justify-content:center;
      transition:all .2s; flex-shrink:0;
    }
    #voiceBtn:hover:not(:disabled) { background:#f97316; color:#fff; }
    #voiceBtn.active { background:#ef4444; color:#fff; }
    #voiceBtn:disabled { opacity:0.45; cursor:not-allowed; }

    #messageInput {
      flex:1; height:44px; padding:0 17px; border-radius:99px;
      border:1.5px solid #fcd34d; background:#fffbeb;
      font-size:14px; color:#1e293b; outline:none;
      font-family:inherit; transition:all .2s;
    }
    #messageInput:focus { background:#fff; border-color:#f97316; box-shadow:0 0 0 3px rgba(249,115,22,0.12); }
    #messageInput::placeholder { color:#94a3b8; }
    #messageInput:disabled { cursor:not-allowed; }

    #sendBtn {
      width:44px; height:44px; border-radius:50%;
      background:linear-gradient(135deg,#f97316,#f59e0b);
      border:none; color:#fff; font-size:17px; cursor:pointer;
      display:flex; align-items:center; justify-content:center;
      box-shadow:0 4px 14px rgba(249,115,22,0.4);
      transition:transform .2s,opacity .2s; flex-shrink:0;
    }
    #sendBtn:hover:not(:disabled) { transform:scale(1.08); }
    #sendBtn:disabled { cursor:not-allowed; }

    .spinner {
      width:18px; height:18px;
      border:2.5px solid rgba(255,255,255,0.4);
      border-top-color:#fff; border-radius:50%;
      animation:spin 0.7s linear infinite;
    }
    .inp-footer { text-align:center; font-size:10px; color:#94a3b8; margin-top:5px; }
  `;

	// ── HTML template ────────────────────────────────────────────────────────
	var HTML = `
    <button id="toggleBtn" class="float" title="किसान AI खोलें">🌾</button>

    <div id="widget">
      <div class="hdr">
        <div class="hdr-left">
          <div class="hdr-avatar">🌾</div>
          <div>
            <h2>किसान AI</h2>
            <div class="hdr-status">
              <span class="hdr-dot pulse"></span>
              <span>फसल विशेषज्ञ • सक्रिय</span>
            </div>
          </div>
        </div>
        <button id="closeBtn">✕</button>
      </div>

      <div id="statusBar">⏳ उत्तर खोजा जा रहा है, कृपया प्रतीक्षा करें...</div>

      <div class="chips" id="chipsRow">
        <button class="chip" data-q="अनार के फूल गिर रहे हैं">🍎 अनार के फूल गिर रहे हैं</button>
        <button class="chip" data-q="टमाटर में कीड़े लग गए हैं">🐛 टमाटर में कीड़े</button>
        <button class="chip" data-q="गेहूं पीली हो रही है">🌾 गेहूं पीला</button>
        <button class="chip" data-q="मिर्च में फफूंद लग गई">🌶️ मिर्च फफूंद</button>
        <button class="chip" data-q="केले मीठे नहीं हो रहे">🍌 केले मीठे नहीं</button>
        <button class="chip" data-q="आलू में झुलसा रोग है">🥔 आलू झुलसा</button>
      </div>

      <div id="messages" class="scroll">
        <div class="msg-row fade-in">
          <div class="msg-av">🤖</div>
          <div class="bubble bot">
            🙏 नमस्ते किसान भाई!<br>
            मैं आपकी फसल, रोग, कीट एवं पोषण संबंधी समस्याओं का समाधान बता सकता हूँ।<br>
            <small style="color:#94a3b8;font-size:12px">कोई भी फसल का नाम लिखकर पूछें।</small>
          </div>
        </div>
      </div>

      <div id="typing">
        <div class="typing-wrap">
          <div class="msg-av">🤖</div>
          <div class="typing-dots">
            <span class="dot1"></span>
            <span class="dot2"></span>
            <span class="dot3"></span>
          </div>
        </div>
      </div>

      <div class="inp-area" id="inputArea">
        <div class="inp-row">
          <button id="voiceBtn" title="वॉइस इनपुट">🎤</button>
          <input id="messageInput" type="text" placeholder="अपनी समस्या लिखें..." />
          <button id="sendBtn" title="भेजें">➤</button>
        </div>
        <div class="inp-footer">🔒 आपकी जानकारी सुरक्षित है</div>
      </div>
    </div>
  `;

	// ── Mount into Shadow DOM ────────────────────────────────────────────────
	var host = document.createElement("div");
	host.id = "kisan-widget-host";
	document.body.appendChild(host);

	var shadow = host.attachShadow({ mode: "open" });

	var styleEl = document.createElement("style");
	styleEl.textContent = CSS;
	shadow.appendChild(styleEl);

	var container = document.createElement("div");
	container.innerHTML = HTML;
	shadow.appendChild(container);

	// ── Grab refs from shadow DOM ────────────────────────────────────────────
	var widget = shadow.getElementById("widget");
	var toggleBtn = shadow.getElementById("toggleBtn");
	var closeBtn = shadow.getElementById("closeBtn");
	var messages = shadow.getElementById("messages");
	var typing = shadow.getElementById("typing");
	var input = shadow.getElementById("messageInput");
	var sendBtn = shadow.getElementById("sendBtn");
	var voiceBtn = shadow.getElementById("voiceBtn");
	var inputArea = shadow.getElementById("inputArea");
	var statusBar = shadow.getElementById("statusBar");
	var chips = shadow.querySelectorAll(".chip");

	// ── Busy lock ────────────────────────────────────────────────────────────
	var isBusy = false;

	function setBusy(busy) {
		isBusy = busy;
		inputArea.classList.toggle("busy", busy);
		input.disabled = busy;
		sendBtn.disabled = busy;
		voiceBtn.disabled = busy;
		chips.forEach(function (c) {
			c.disabled = busy;
		});
		sendBtn.innerHTML = busy ? '<div class="spinner"></div>' : "➤";
		statusBar.classList.toggle("show", busy);
		if (busy) {
			typing.classList.add("show");
			scrollBottom();
		} else {
			typing.classList.remove("show");
		}
	}

	// ── Toggle ───────────────────────────────────────────────────────────────
	toggleBtn.addEventListener("click", function () {
		widget.classList.add("open");
		toggleBtn.classList.add("hidden");
		setTimeout(function () {
			input.focus();
		}, 200);
	});

	closeBtn.addEventListener("click", function () {
		widget.classList.remove("open");
		toggleBtn.classList.remove("hidden");
	});

	// ── Helpers ──────────────────────────────────────────────────────────────
	function scrollBottom() {
		messages.scrollTop = messages.scrollHeight;
	}

	function esc(s) {
		return String(s).replace(/[&<>"']/g, function (c) {
			return {
				"&": "&amp;",
				"<": "&lt;",
				">": "&gt;",
				'"': "&quot;",
				"'": "&#039;",
			}[c];
		});
	}

	function addUser(text) {
		var d = document.createElement("div");
		d.className = "msg-row user fade-in";
		d.innerHTML =
			'<div class="msg-av">👤</div><div class="bubble user">' +
			esc(text) +
			"</div>";
		messages.appendChild(d);
		scrollBottom();
	}

	function addBot(text) {
		var d = document.createElement("div");
		d.className = "msg-row fade-in";
		d.innerHTML =
			'<div class="msg-av">🤖</div><div class="bubble bot"><span class="t"></span></div>';
		messages.appendChild(d);
		var span = d.querySelector(".t");
		var i = 0;
		var iv = setInterval(function () {
			if (i < text.length) {
				span.textContent += text[i++];
				scrollBottom();
			} else {
				clearInterval(iv);
			}
		}, 20);
		scrollBottom();
	}

	// ── Send ─────────────────────────────────────────────────────────────────
	function send() {
		if (isBusy) return;
		var msg = input.value.trim();
		if (!msg) return;

		addUser(msg);
		input.value = "";
		setBusy(true);

		fetch(API_BASE + "/search?q=" + encodeURIComponent(msg))
			.then(function (res) {
				return res.json();
			})
			.then(function (data) {
				if (Array.isArray(data) && data.length > 0) {
					addBot(data[0].solution || "समाधान उपलब्ध नहीं।");
				} else if (data.message) {
					addBot(data.message);
				} else {
					addBot("क्षमा करें, इस समस्या का समाधान उपलब्ध नहीं है।");
				}
			})
			.catch(function () {
				addBot("⚠️ सर्वर से कनेक्ट नहीं हो पाया। कृपया API सर्वर चालू करें।");
			})
			.finally(function () {
				setBusy(false);
				input.focus();
			});
	}

	sendBtn.addEventListener("click", send);
	input.addEventListener("keypress", function (e) {
		if (e.key === "Enter" && !isBusy) {
			e.preventDefault();
			send();
		}
	});

	// Chip clicks
	chips.forEach(function (chip) {
		chip.addEventListener("click", function () {
			if (isBusy) return;
			input.value = chip.getAttribute("data-q");
			send();
		});
	});

	// ── Voice ────────────────────────────────────────────────────────────────
	var SR = window.SpeechRecognition || window.webkitSpeechRecognition;

	if (SR) {
		var rec = new SR();
		rec.lang = "hi-IN";
		rec.continuous = false;
		rec.interimResults = true;
		var listening = false;

		voiceBtn.addEventListener("click", function () {
			if (isBusy) return;
			if (listening) {
				rec.stop();
				return;
			}
			try {
				rec.start();
				listening = true;
				voiceBtn.classList.add("active");
				input.value = "🎤 सुन रहा हूं...";
				input.disabled = true;
			} catch (e) {
				addBot("❌ माइक्रोफ़ोन एक्सेस नहीं मिला।");
			}
		});

		rec.onresult = function (e) {
			var last = e.results[e.results.length - 1];
			input.value = last[0].transcript;
			if (last.isFinal) {
				input.disabled = false;
				rec.stop();
				setTimeout(function () {
					if (input.value.trim()) send();
				}, 350);
			}
		};

		rec.onerror = function (e) {
			listening = false;
			voiceBtn.classList.remove("active");
			input.value = "";
			input.disabled = false;
			var map = {
				"no-speech": "कोई आवाज़ नहीं सुनाई दी।",
				"not-allowed": "माइक्रोफ़ोन अनुमति अस्वीकृत।",
				network: "नेटवर्क त्रुटि।",
			};
			addBot("⚠️ " + (map[e.error] || "वॉइस त्रुटि: " + e.error));
		};

		rec.onend = function () {
			listening = false;
			voiceBtn.classList.remove("active");
			if (input.disabled && input.value === "🎤 सुन रहा हूं...") {
				input.value = "";
				input.disabled = false;
			}
		};
	} else {
		// Fallback: server-side Vosk via MediaRecorder
		var recorder,
			chunks = [],
			recording = false;

		voiceBtn.addEventListener("click", function () {
			if (isBusy) return;
			if (recording) {
				recorder.stop();
				return;
			}

			navigator.mediaDevices
				.getUserMedia({ audio: true })
				.then(function (stream) {
					recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
					chunks = [];
					recorder.ondataavailable = function (e) {
						chunks.push(e.data);
					};
					recorder.onstop = function () {
						recording = false;
						voiceBtn.classList.remove("active");
						stream.getTracks().forEach(function (t) {
							t.stop();
						});
						input.value = "⏳ पहचान हो रही है...";
						input.disabled = true;

						var fd = new FormData();
						fd.append(
							"audio",
							new Blob(chunks, { type: "audio/wav" }),
							"voice.wav",
						);

						fetch(API_BASE + "/voice", { method: "POST", body: fd })
							.then(function (r) {
								return r.json();
							})
							.then(function (data) {
								if (data.success && data.transcript) {
									input.value = data.transcript;
									input.disabled = false;
									setTimeout(function () {
										send();
									}, 350);
								} else {
									input.value = "";
									input.disabled = false;
									addBot("⚠️ " + (data.message || "आवाज़ नहीं पहचानी गई।"));
								}
							})
							.catch(function () {
								input.value = "";
								input.disabled = false;
								addBot("❌ वॉइस सेवा अनुपलब्ध।");
							});
					};

					recorder.start();
					recording = true;
					voiceBtn.classList.add("active");
					input.value = "🎤 रिकॉर्ड हो रहा है... (रोकने के लिए टैप करें)";
					input.disabled = true;
				})
				.catch(function () {
					addBot("❌ माइक्रोफ़ोन अनुमति आवश्यक है।");
				});
		});
	}
})();
