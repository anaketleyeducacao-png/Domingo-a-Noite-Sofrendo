import base64
import json
import os
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

# Configuração da página Streamlit
st.set_page_config(
    page_title="Domingo de Noite Sofrendo",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dimensões do jogo
WIDTH = 1280
HEIGHT = 720

# Dicionário de tipos MIME
MIME_BY_SUFFIX = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

def get_local_file_as_data_uri(file_name):
    base_path = Path(__file__).parent.parent
    file_path = base_path / file_name
    if not file_path.exists():
        return None
    suffix = file_path.suffix.lower()
    mime = MIME_BY_SUFFIX.get(suffix, "application/octet-stream")
    try:
        with open(file_path, "rb") as f:
            payload = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{payload}"
    except Exception:
        return None

def file_to_data_uri(uploaded_file, file_name, fallback_mime="application/octet-stream"):
    if uploaded_file is not None:
        suffix = Path(uploaded_file.name).suffix.lower()
        mime = MIME_BY_SUFFIX.get(suffix, fallback_mime)
        payload = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
        return f"data:{mime};base64,{payload}", "Upload"
    uri = get_local_file_as_data_uri(file_name)
    if uri:
        return uri, "Automático"
    return "", "Não encontrado"

st.title("Domingo de Noite Sofrendo — Versão Completa")

with st.sidebar:
    st.header("🎮 Configurações")
    
    st.subheader("📁 Status dos Arquivos")
    audio_file = st.file_uploader("Trocar Música", type=["mp3", "wav", "ogg"])
    audio_uri, audio_status = file_to_data_uri(audio_file, "musica.mp3", "audio/mpeg")
    st.write(f"🎵 **Música:** {audio_status}")
    
    st.divider()
    st.subheader("🖼️ Sprites & Chroma Key")
    chroma_sensitivity = st.slider("Sensibilidade do Verde", 0, 255, 100)
    
    col1, col2 = st.columns(2)
    with col1:
        u_idle = st.file_uploader("Idle", type=["png", "jpg", "webp"], key="u_idle")
        idle_uri, idle_status = file_to_data_uri(u_idle, "sprite_p.png")
        u_down = st.file_uploader("Baixo", type=["png", "jpg", "webp"], key="u_down")
        down_uri, down_status = file_to_data_uri(u_down, "sprite_b.png")
        u_right = st.file_uploader("Direita", type=["png", "jpg", "webp"], key="u_right")
        right_uri, right_status = file_to_data_uri(u_right, "sprite_d.png")
    with col2:
        u_left = st.file_uploader("Esquerda", type=["png", "jpg", "webp"], key="u_left")
        left_uri, left_status = file_to_data_uri(u_left, "sprite_e.png")
        u_up = st.file_uploader("Cima", type=["png", "jpg", "webp"], key="u_up")
        up_uri, up_status = file_to_data_uri(u_up, "sprite_c.png")

    st.divider()
    st.subheader("⚙️ Dificuldade")
    bpm = st.slider("BPM", min_value=60, max_value=240, value=172)
    note_speed = st.slider("Velocidade", min_value=100, max_value=800, value=300)
    note_freq = st.slider("Densidade", min_value=0.2, max_value=3.0, value=1.0)
    seed = st.number_input("Seed", min_value=1, value=12345)

assets = {
    "audio": audio_uri,
    "sprites": {
        "idle": idle_uri,
        "left": left_uri,
        "down": down_uri,
        "up": up_uri,
        "right": right_uri,
    },
    "config": {
        "width": WIDTH,
        "height": HEIGHT,
        "bpm": bpm,
        "noteSpeed": note_speed,
        "noteFreq": note_freq,
        "seed": int(seed),
        "chromaSensitivity": chroma_sensitivity
    },
}

config_json = json.dumps(assets, ensure_ascii=False)

html_code = f"""
<div id="game-container">
    <div class="controls">
        <button id="start-btn">JOGAR / REINICIAR</button>
        <span id="game-status">Aguardando...</span>
    </div>
    <canvas id="gameCanvas" width="{WIDTH}" height="{HEIGHT}" tabindex="0"></canvas>
</div>

<style>
    #game-container {{ display: flex; flex-direction: column; align-items: center; font-family: 'Segoe UI', Tahoma, sans-serif; color: white; }}
    .controls {{ width: {WIDTH}px; max-width: 100%; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
    #start-btn {{ padding: 12px 24px; background: #ff4b4b; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; }}
    #start-btn:hover {{ background: #ff3333; }}
    #gameCanvas {{ background: #146464; border: 5px solid #262730; border-radius: 12px; outline: none; max-width: 100%; height: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
    #gameCanvas:focus {{ border-color: #ff4b4b; }}
</style>

<script>
(() => {{
    const assets = {config_json};
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const startBtn = document.getElementById('start-btn');
    const statusTxt = document.getElementById('game-status');

    const COLORS = {{
        bg: '#146464', dark: '#141428', gray: '#3c3c50', white: '#ffffff',
        hitLine: '#c8c8ff', perfect: '#ffdc32', good: '#50dc78', miss: '#dc3c3c',
        combo: '#ffb400', lanes: ['#ffffff', '#ffa032', '#3cffff', '#f0a0f0']
    }};

    const GAME_CFG = {{
        laneCount: 4, laneWidth: 60, gap: 12, startX: 30,
        hitY: {HEIGHT} - 100, noteH: 24, charX: 630, charY: {HEIGHT} - 80, spriteH: 350
    }};

    const KEY_MAP = {{ 'ArrowLeft': 0, 'ArrowDown': 1, 'ArrowUp': 2, 'ArrowRight': 3, 'a': 0, 's': 1, 'j': 2, 'k': 3, 'A': 0, 'S': 1, 'J': 2, 'K': 3 }};

    function removeGreen(img) {{
        const c = document.createElement('canvas');
        c.width = img.width; c.height = img.height;
        const x = c.getContext('2d');
        x.drawImage(img, 0, 0);
        const d = x.getImageData(0, 0, c.width, c.height);
        const s = assets.config.chromaSensitivity;
        for (let i=0; i<d.data.length; i+=4) {{
            if (d.data[i+1] > s && d.data[i+1] > d.data[i] && d.data[i+1] > d.data[i+2]) d.data[i+3] = 0;
        }}
        x.putImageData(d, 0, 0);
        const n = new Image(); n.src = c.toDataURL(); return n;
    }}

    const sprites = {{}};
    const spritePromises = Object.entries(assets.sprites).map(([name, src]) => {{
        if (!src) return Promise.resolve();
        return new Promise(r => {{
            const i = new Image(); i.onload = () => {{ sprites[name] = removeGreen(i); r(); }}; i.src = src;
        }});
    }});

    const audio = assets.audio ? new Audio(assets.audio) : null;

    class Game {{
        constructor() {{ this.reset(); }}
        reset() {{
            this.running = false; this.score = 0; this.combo = 0; this.health = 100;
            this.feedback = ""; this.fbT = 0; this.pose = "idle"; this.poseT = 0;
            this.flash = [0,0,0,0]; this.gameOver = false; this.finished = false;
            this.rng = assets.config.seed; this.chart = this.genChart();
            if (audio) {{ audio.pause(); audio.currentTime = 0; }}
        }}
        random() {{ this.rng = (this.rng * 1664525 + 1013904223) >>> 0; return this.rng / 4294967296; }}
        genChart() {{
            const n = []; const dur = audio?.duration || 120; const bi = 60 / assets.config.bpm;
            let t = 3.0;
            while (t < dur - 1.0) {{
                const l = Math.floor(this.random() * 4); n.push({{ lane: l, time: t, hit: false, miss: false }});
                if (this.random() < 0.2) n.push({{ lane: (l+1)%4, time: t, hit: false, miss: false }});
                t += bi * [0.5, 1, 1, 1, 2][Math.floor(this.random()*5)] * assets.config.noteFreq;
            }}
            return n.sort((a,b) => a.time - b.time);
        }}
        start() {{ this.reset(); this.running = true; this.startTime = performance.now(); if (audio) audio.play(); statusTxt.textContent = "JOGANDO!"; }}
        
        update(now) {{
            if (!this.running || this.gameOver || this.finished) return;
            const ct = (now - this.startTime) / 1000;
            for (const n of this.chart) {{
                if (!n.hit && !n.miss && n.time < ct - 0.25) {{ n.miss = true; this.triggerMiss(); }}
            }}
            if (this.fbT > 0) this.fbT -= 1/60;
            if (this.poseT > 0) this.poseT -= 1/60; else this.pose = "idle";
            for (let i=0; i<4; i++) if (this.flash[i] > 0) this.flash[i] -= 1/60;
            if (this.health <= 0) {{ this.gameOver = true; this.running = false; if (audio) audio.pause(); statusTxt.textContent = "GAME OVER!"; }}
            if (ct > (audio?.duration || 120) + 1) {{ this.finished = true; this.running = false; statusTxt.textContent = "CONCLUÍDO!"; }}
        }}

        triggerMiss() {{
            this.combo = 0; this.health = Math.max(0, this.health - 8);
            this.feedback = "MISS"; this.fbT = 0.4;
        }}

        handle(key) {{
            const l = KEY_MAP[key]; if (l === undefined || !this.running) return;
            const ct = (performance.now() - this.startTime) / 1000;
            let b = null; let d = 999;
            for (const n of this.chart) if (!n.hit && !n.miss && n.lane === l) {{ const df = Math.abs(n.time - ct); if (df < d) {{ d = df; b = n; }} }}
            if (!b || d > 0.25) return;
            this.flash[l] = 0.15; this.pose = ["left", "down", "up", "right"][l]; this.poseT = 0.25;
            if (d < 0.08) {{ b.hit = true; this.score += 300; this.combo++; this.feedback = "PERFECT"; this.fbT = 0.6; this.health = Math.min(100, this.health+5); }}
            else {{ b.hit = true; this.score += 100; this.combo++; this.feedback = "GOOD"; this.fbT = 0.5; this.health = Math.min(100, this.health+2); }}
        }}

        roundRect(x, y, w, h, r, fill) {{
            ctx.beginPath(); ctx.moveTo(x+r, y); ctx.arcTo(x+w, y, x+w, y+h, r); ctx.arcTo(x+w, y+h, x, y+h, r); ctx.arcTo(x, y+h, x, y, r); ctx.arcTo(x, y, x+w, y, r); ctx.closePath();
            if (fill) ctx.fill(); else ctx.stroke();
        }}

        draw() {{
            ctx.fillStyle = COLORS.bg; ctx.fillRect(0, 0, {WIDTH}, {HEIGHT});
            const ct = this.running ? (performance.now() - this.startTime) / 1000 : 0;
            ctx.strokeStyle = COLORS.gray; ctx.beginPath(); ctx.moveTo(370, 0); ctx.lineTo(370, {HEIGHT}); ctx.stroke();
            for (let i=0; i<4; i++) {{
                const x = GAME_CFG.startX + i * 72;
                ctx.fillStyle = COLORS.dark; ctx.fillRect(x, 0, 60, {HEIGHT});
                ctx.strokeStyle = COLORS.lanes[i]; ctx.strokeRect(x, 0, 60, {HEIGHT});
            }}
            ctx.strokeStyle = COLORS.hitLine; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(GAME_CFG.startX-5, GAME_CFG.hitY); ctx.lineTo(GAME_CFG.startX+283, GAME_CFG.hitY); ctx.stroke(); ctx.lineWidth = 1;
            for (const n of this.chart) {{
                if (n.hit || n.miss) continue;
                const td = n.time - ct; if (td > 2 || td < -0.5) continue;
                const y = GAME_CFG.hitY - td * assets.config.noteSpeed - 12;
                const x = GAME_CFG.startX + n.lane * 72;
                ctx.fillStyle = COLORS.lanes[n.lane];
                this.roundRect(x+4, y, 52, 24, 8, true);
                ctx.strokeStyle = "white"; this.roundRect(x+4, y, 52, 24, 8, false);
            }}
            const labels = ["◄", "▼", "▲", "►"];
            for (let i=0; i<4; i++) {{
                const x = GAME_CFG.startX + i * 72;
                ctx.fillStyle = this.flash[i] > 0 ? COLORS.lanes[i] : COLORS.gray;
                this.roundRect(x+4, GAME_CFG.hitY-18, 52, 36, 10, true);
                ctx.fillStyle = "white"; ctx.font = "bold 20px monospace"; ctx.textAlign = "center";
                ctx.fillText(labels[i], x+30, GAME_CFG.hitY+7);
            }}
            const img = sprites[this.pose] || sprites.idle;
            if (img) {{ const r = 350/img.height; ctx.drawImage(img, 630-img.width*r/2, {HEIGHT}-80-350, img.width*r, 350); }}
            else {{ ctx.strokeStyle = "white"; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(630, {HEIGHT}-300, 30, 0, Math.PI*2); ctx.moveTo(630, {HEIGHT}-270); ctx.lineTo(630, {HEIGHT}-150); ctx.stroke(); }}
            ctx.textAlign = "left"; ctx.fillStyle = "white"; ctx.font = "bold 28px monospace";
            ctx.fillText("SCORE: " + String(this.score).padStart(8, '0'), 400, 60);
            if (this.combo >= 3) {{ ctx.fillStyle = COLORS.combo; ctx.fillText(this.combo + "x COMBO", 400, 100); }}
            if (this.fbT > 0) {{ 
                ctx.globalAlpha = Math.min(1, this.fbT / 0.2);
                ctx.fillStyle = this.feedback === "PERFECT" ? COLORS.perfect : (this.feedback === "MISS" ? COLORS.miss : COLORS.good);
                ctx.font = "bold 45px monospace"; ctx.fillText(this.feedback, GAME_CFG.startX, GAME_CFG.hitY-60);
                ctx.globalAlpha = 1;
            }}
            ctx.fillStyle = COLORS.gray; this.roundRect(400, {HEIGHT}-50, 300, 20, 10, true);
            ctx.fillStyle = this.health > 25 ? COLORS.good : COLORS.miss;
            this.roundRect(400, {HEIGHT}-50, 300*(this.health/100), 20, 10, true);
            ctx.strokeStyle = "white"; this.roundRect(400, {HEIGHT}-50, 300, 20, 10, false);
            if (this.gameOver) this.drawOverlay("GAME OVER", COLORS.miss, "HP zerado!");
            if (this.finished) this.drawOverlay("CONCLUÍDO!", COLORS.perfect, "Score final: " + this.score);
            if (!this.running && !this.gameOver && !this.finished) {{ this.drawOverlay("PRONTO?", "white", "Clique em JOGAR ou aperte ENTER"); }}
        }}

        drawOverlay(txt, color, sub) {{
            ctx.fillStyle = "rgba(0,0,0,0.8)"; ctx.fillRect(0,0,{WIDTH},{HEIGHT});
            ctx.textAlign = "center"; ctx.fillStyle = color; ctx.font = "bold 70px monospace";
            ctx.fillText(txt, {WIDTH}/2, {HEIGHT}/2);
            ctx.fillStyle = "white"; ctx.font = "24px monospace"; ctx.fillText(sub, {WIDTH}/2, {HEIGHT}/2 + 60);
        }}
    }}

    const game = new Game();
    function loop(n) {{ game.update(n); game.draw(); requestAnimationFrame(loop); }}
    startBtn.onclick = () => {{ canvas.focus(); game.start(); }};
    canvas.onkeydown = (e) => {{
        if (e.key === 'Enter' && !game.running) game.start();
        game.handle(e.key);
    }};
    Promise.all(spritePromises).then(() => {{ requestAnimationFrame(loop); statusTxt.textContent = "Pronto!"; }});
}})();
</script>
"""

components.html(html_code, height=800, scrolling=False)

st.divider()
st.markdown("""
### ⌨️ Controles
- **Setas** ou **A S J K** para as notas.
- **ENTER** para iniciar/reiniciar.
- A música **para automaticamente** se você perder.
""")
