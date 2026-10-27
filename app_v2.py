import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="2인용 탱크 전쟁",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stApp {
    background: #101820;
    color: white;
}
.block-container {
    padding-top: 1.5rem;
    max-width: 1250px;
}
h1, h2, h3, p {
    color: white;
}
</style>
""", unsafe_allow_html=True)

# 게임 시작 여부 세션 상태 관리
if "game_started" not in st.session_state:
    st.session_state.game_started = False

# ==========================================
# 1. 시작 전 (대기 / 안내) 화면
# ==========================================
if not st.session_state.game_started:
    st.title("🎮 2인용 탱크 전쟁")
    st.caption("두 명이 함께 싸우는 2D 탱크 배틀!")

    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#182d3b,#263d32);
        border:2px solid #5d8d73;
        border-radius:18px;
        padding:40px 20px;
        text-align:center;
        margin:20px 0;
    ">
        <div style="font-size:75px;">🚜 💥 🚜</div>
        <h1 style="color:#b5ffb8; margin-top:10px;">TANK WAR</h1>
        <p style="font-size:18px; color:#d0e6d5;">
            상대방 탱크를 조준하여 먼저 제압하세요!
        </p>
        <p style="color:#8ebf9b; font-size:14px;">한 화면에 담긴 전장 · 장애물 엄폐 · 초고속 회전 조작</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🎮 조작 방법")

    left, right = st.columns(2)

    with left:
        st.markdown("""
        ### 🟢 1P 초록 탱크
        - `W` : 전진
        - `SPACE` : 대포 발사
        """)

    with right:
        st.markdown("""
        ### 🔴 2P 빨간 탱크
        - `O` : 전진
        - `P` : 대포 발사
        """)

    st.info(
        "💡 탱크는 가만히 있으면 매우 빠르게 자동 회전합니다. "
        "전진 키(W/O)를 누르면 회전을 멈추고 바라보는 방향으로 이동합니다!"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 게임 시작", type="primary", use_container_width=True):
        st.session_state.game_started = True
        st.rerun()

# ==========================================
# 2. 게임 시작 후 (실제 게임) 화면
# ==========================================
else:
    top_col1, top_col2 = st.columns([4, 1])
    with top_col1:
        st.title("⚔️ TANK WAR - 전투 진행 중")
    with top_col2:
        if st.button("↩️ 메인 메뉴로", use_container_width=True):
            st.session_state.game_started = False
            st.rerun()

    game_html = r"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
      * { box-sizing: border-box; }
      body {
        margin: 0;
        background: #101820;
        color: white;
        font-family: Arial, sans-serif;
        overflow: hidden;
      }
      #hud {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        padding: 10px 16px;
        background: #1c2c32;
        border: 1px solid #42604d;
        border-radius: 10px 10px 0 0;
        font-weight: bold;
        font-size: 15px;
      }
      #game {
        display: block;
        width: 100%;
        height: auto;
        aspect-ratio: 1000 / 650;
        background: #344b38;
        border: 2px solid #52785b;
        outline: none;
        touch-action: none;
      }
      #help {
        font-size: 13px;
        color: #c9d8cc;
        text-align: center;
        padding: 8px;
        line-height: 1.6;
      }
      #restart {
        margin-top: 6px;
        padding: 6px 16px;
        border: 1px solid #7fbd8a;
        border-radius: 8px;
        background: #213b2b;
        color: white;
        font-weight: bold;
        cursor: pointer;
      }
      #restart:hover { background: #31543d; }
    </style>
    </head>
    <body>
      <div id="hud">
        <span style="color:#69ff8c">🟢 P1 HP: <span id="hp1">3</span></span>
        <span id="status">TANK WAR</span>
        <span style="color:#ff7777">P2 HP: <span id="hp2">3</span> 🔴</span>
      </div>
      <canvas id="game" width="1000" height="650" tabindex="0"></canvas>
      <div id="help">
        🟢 P1: W (전진) / SPACE (발사) &nbsp;|&nbsp; 🔴 P2: O (전진) / P (발사)
        <br>
        <button id="restart" type="button" onclick="location.reload()">🔄 판 다시 시작</button>
      </div>

    <script>
    (() => {
      const canvas = document.getElementById('game');
      const ctx = canvas.getContext('2d');
      const W = 1000, H = 650;
      
      const MW = 1300, MH = 850;
      const keys = new Set();

      let running = true;
      let last = performance.now();
      let now = 0;
      let bullets = [];
      let particles = [];
      let winner = '';
      let audio = null;

      const obstacles = [];

      function addRect(x, y, w, h, type='rock', hp=2) {
        obstacles.push({x, y, w, h, type, hp});
      }

      // 맵 가장자리 벽 (부서지지 않음)
      addRect(0, 0, MW, 30, 'wall', 999);
      addRect(0, MH-30, MW, 30, 'wall', 999);
      addRect(0, 0, 30, MH, 'wall', 999);
      addRect(MW-30, 0, 30, MH, 'wall', 999);

      // 장애물 배치 (기본 HP: 2)
      [
        [350, 200, 120, 50], [830, 200, 120, 50],
        [550, 400, 200, 50],
        [350, 600, 120, 50], [830, 600, 120, 50],
        [200, 350, 50, 150], [1050, 350, 50, 150]
      ].forEach(a => addRect(a[0], a[1], a[2], a[3], 'rock', 2));

      const tanks = [
        {
          x: 120, y: 120, angle: 0,
          color: '#42e66e', dark: '#167b37',
          key: 'w', fire: ' ', hp: 3, lastShot: -2000
        },
        {
          x: MW - 120, y: MH - 120, angle: Math.PI,
          color: '#ff5656', dark: '#9b2525',
          key: 'o', fire: 'p', hp: 3, lastShot: -2000
        }
      ];

      function sound() {
        try {
          audio = audio || new (window.AudioContext || window.webkitAudioContext)();
          if (audio.state === 'suspended') audio.resume();

          const t = audio.currentTime;
          const osc = audio.createOscillator();
          const gain = audio.createGain();

          osc.type = 'triangle';
          osc.frequency.setValueAtTime(150, t);
          osc.frequency.exponentialRampToValueAtTime(42, t + 0.20);

          gain.gain.setValueAtTime(0.0001, t);
          gain.gain.exponentialRampToValueAtTime(0.32, t + 0.012);
          gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.24);

          osc.connect(gain);
          gain.connect(audio.destination);
          osc.start(t);
          osc.stop(t + 0.25);
        } catch(e) {}
      }

      function circleRect(cx, cy, r, o) {
        const px = Math.max(o.x, Math.min(cx, o.x + o.w));
        const py = Math.max(o.y, Math.min(cy, o.y + o.h));
        const dx = cx - px, dy = cy - py;
        return dx*dx + dy*dy < r*r;
      }

      function blocked(x, y, r) {
        if (x < r || y < r || x > MW-r || y > MH-r) return true;
        return obstacles.some(o => o.hp > 0 && circleRect(x, y, r, o));
      }

      function tankBlocked(t, x, y) {
        if (blocked(x,y,15)) return true;
        return tanks.some(other =>
          other !== t && Math.hypot(other.x-x, other.y-y) < 32
        );
      }

      function shoot(t, index) {
        if (now - t.lastShot < 2000) return;
        t.lastShot = now;

        const a = t.angle;
        const sx = t.x + Math.cos(a)*27;
        const sy = t.y + Math.sin(a)*27;

        bullets.push({
          x:sx, y:sy,
          vx:Math.cos(a)*7.2,
          vy:Math.sin(a)*7.2,
          owner:index,
          life:220
        });

        sound();

        for(let i=0;i<7;i++) {
          particles.push({
            x:sx, y:sy,
            vx:(Math.random()-.5)*3,
            vy:(Math.random()-.5)*3,
            life:16,
            color:'#ffcf73'
          });
        }
      }

      function drawTank(t) {
        ctx.save();
        ctx.translate(t.x,t.y);
        ctx.rotate(t.angle);

        // 궤도
        ctx.fillStyle = '#222a27';
        ctx.fillRect(-18,-13,36,8);
        ctx.fillRect(-18,5,36,8);

        // 몸체
        ctx.fillStyle = t.dark;
        ctx.fillRect(-15,-10,30,20);

        ctx.fillStyle = t.color;
        ctx.fillRect(-12,-8,24,16);

        // 포신
        ctx.fillStyle = '#d6ded8';
        ctx.fillRect(1,-3,27,6);

        // 포탑
        ctx.fillStyle = t.dark;
        ctx.beginPath();
        ctx.arc(0,0,7,0,Math.PI*2);
        ctx.fill();

        ctx.restore();

        ctx.fillStyle = 'white';
        ctx.font = 'bold 13px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(t===tanks[0]?'P1':'P2',t.x,t.y-23);

        // 체력 표시
        ctx.fillStyle = '#1b1b1b';
        ctx.fillRect(t.x-17,t.y+19,34,5);
        ctx.fillStyle = t.color;
        ctx.fillRect(t.x-17,t.y+19,34*Math.max(0,t.hp)/3,5);
      }

      function drawObstacle(o) {
        if (o.hp <= 0) return; // 부서진 장애물은 그리지 않음

        if(o.type==='wall') {
          ctx.fillStyle='#59665a';
          ctx.fillRect(o.x,o.y,o.w,o.h);
          ctx.strokeStyle='#829184';
          ctx.lineWidth=2;
          ctx.strokeRect(o.x,o.y,o.w,o.h);
          return;
        }

        ctx.fillStyle='#25342b';
        ctx.fillRect(o.x+4,o.y+5,o.w,o.h);

        ctx.fillStyle='#677b63';
        ctx.fillRect(o.x,o.y,o.w,o.h);

        ctx.fillStyle='#83977b';
        ctx.fillRect(o.x+4,o.y+4,Math.max(0,o.w-8),4);

        ctx.strokeStyle='#344a38';
        ctx.lineWidth=2;
        ctx.strokeRect(o.x,o.y,o.w,o.h);

        // 1번 맞아서 HP가 1 남았을 때 (금 간 표현)
        if (o.hp === 1) {
          ctx.strokeStyle = '#1a261e';
          ctx.lineWidth = 2;
          ctx.beginPath();
          // X자 형태의 금무늬 추가
          ctx.moveTo(o.x + o.w * 0.2, o.y + o.h * 0.2);
          ctx.lineTo(o.x + o.w * 0.8, o.y + o.h * 0.8);
          ctx.moveTo(o.x + o.w * 0.8, o.y + o.h * 0.2);
          ctx.lineTo(o.x + o.w * 0.2, o.y + o.h * 0.8);
          ctx.stroke();
        }
      }

      function update(dt) {
        if(!running) return;

        const speed = 3.3 * dt;
        const rotationSpeed = 0.021 * dt;

        tanks.forEach((t,i) => {
          const moving = keys.has(t.key);

          if(moving) {
            const nx = t.x + Math.cos(t.angle)*speed;
            const ny = t.y + Math.sin(t.angle)*speed;

            if(!tankBlocked(t,nx,ny)) {
              t.x=nx;
              t.y=ny;
            }
          } else {
            t.angle += rotationSpeed;
          }

          if(keys.has(t.fire)) shoot(t,i);
        });

        bullets.forEach(b => {
          b.x += b.vx*dt;
          b.y += b.vy*dt;
          b.life -= dt;

          // 장애물 충돌 검사
          obstacles.forEach(o => {
            if (o.hp > 0 && circleRect(b.x, b.y, 4, o)) {
              b.life = 0; // 총알 소멸
              
              if (o.type !== 'wall') {
                o.hp--; // 장애물 내구도 감소 (2 -> 1 -> 0)
                
                // 파편 효과 발생
                for(let k=0; k<8; k++) {
                  particles.push({
                    x: b.x, y: b.y,
                    vx: (Math.random() - .5) * 5,
                    vy: (Math.random() - .5) * 5,
                    life: 20,
                    color: '#83977b'
                  });
                }
              }
            }
          });

          if(blocked(b.x,b.y,4)) b.life=0;

          tanks.forEach((t,i) => {
            if(i!==b.owner && t.hp>0 && Math.hypot(t.x-b.x,t.y-b.y)<17) {
              t.hp--;
              b.life=0;

              for(let k=0;k<16;k++) {
                particles.push({
                  x:b.x,y:b.y,
                  vx:(Math.random()-.5)*6,
                  vy:(Math.random()-.5)*6,
                  life:25,
                  color:Math.random()>.5?'#ffb347':'#ff6262'
                });
              }

              if(t.hp<=0) {
                winner = i===0 ? '🔴 P2 승리!' : '🟢 P1 승리!';
                running=false;
              }
            }
          });
        });

        bullets=bullets.filter(b=>b.life>0);

        particles.forEach(p=>{
          p.x+=p.vx*dt;
          p.y+=p.vy*dt;
          p.life-=dt;
        });
        particles=particles.filter(p=>p.life>0);
      }

      function render() {
        ctx.clearRect(0,0,W,H);
        ctx.save();

        const p1 = tanks[0], p2 = tanks[1];
        const midX = (p1.x + p2.x) / 2;
        const midY = (p1.y + p2.y) / 2;

        const dx = Math.abs(p1.x - p2.x) + 220;
        const dy = Math.abs(p1.y - p2.y) + 220;

        let scale = Math.min(W / dx, H / dy, 1.0);
        scale = Math.max(scale, 0.65);

        let camX = midX - (W / (2 * scale));
        let camY = midY - (H / (2 * scale));

        camX = Math.max(0, Math.min(MW - W / scale, camX));
        camY = Math.max(0, Math.min(MH - H / scale, camY));

        ctx.scale(scale, scale);
        ctx.translate(-camX, -camY);

        ctx.fillStyle='#344b38';
        ctx.fillRect(0,0,MW,MH);

        // 바닥 격자
        ctx.strokeStyle='rgba(210,235,200,0.09)';
        ctx.lineWidth=1;
        for(let x=0;x<=MW;x+=50) {
          ctx.beginPath();
          ctx.moveTo(x,0); ctx.lineTo(x,MH); ctx.stroke();
        }
        for(let y=0;y<=MH;y+=50) {
          ctx.beginPath();
          ctx.moveTo(0,y); ctx.lineTo(MW,y); ctx.stroke();
        }

        obstacles.forEach(drawObstacle);
        tanks.forEach(drawTank);

        bullets.forEach(b=>{
          ctx.fillStyle='#ffdb69';
          ctx.beginPath();
          ctx.arc(b.x,b.y,5,0,Math.PI*2);
          ctx.fill();

          ctx.strokeStyle='#fff2ad';
          ctx.lineWidth=2;
          ctx.beginPath();
          ctx.moveTo(b.x-b.vx*1.7,b.y-b.vy*1.7);
          ctx.lineTo(b.x,b.y);
          ctx.stroke();
        });

        particles.forEach(p=>{
          ctx.globalAlpha=Math.max(0,p.life/25);
          ctx.fillStyle=p.color;
          ctx.beginPath();
          ctx.arc(p.x,p.y,3,0,Math.PI*2);
          ctx.fill();
        });
        ctx.globalAlpha=1;

        ctx.restore();

        document.getElementById('hp1').textContent=tanks[0].hp;
        document.getElementById('hp2').textContent=tanks[1].hp;

        const cd1=Math.max(0,2-(now-tanks[0].lastShot)/1000);
        const cd2=Math.max(0,2-(now-tanks[1].lastShot)/1000);

        document.getElementById('status').textContent =
          winner || `P1 쿨타임 ${cd1.toFixed(1)}s | P2 쿨타임 ${cd2.toFixed(1)}s`;

        if(!running) {
          ctx.fillStyle='rgba(0,0,0,0.72)';
          ctx.fillRect(0,0,W,H);
          ctx.textAlign='center';
          ctx.fillStyle='#ffffff';
          ctx.font='bold 44px Arial';
          ctx.fillText(winner,W/2,H/2-10);
          ctx.font='18px Arial';
          ctx.fillText('아래 [🔄 판 다시 시작] 버튼을 누르면 재경기할 수 있습니다.',W/2,H/2+35);
        }
      }

      function frame(ts) {
        const dt=Math.min(2.5,(ts-last)/16.667);
        last=ts;
        now=ts;
        update(dt);
        render();
        requestAnimationFrame(frame);
      }

      function normalizeKey(e) {
        if(e.code==='Space') return ' ';
        return e.key.toLowerCase();
      }

      window.addEventListener('keydown',e=>{
        const k=normalizeKey(e);
        if(['w','o','p',' '].includes(k)) {
          e.preventDefault();
          keys.add(k);
          if(k===' ' || k==='p') {
            if(audio && audio.state==='suspended') audio.resume();
          }
        }
      },{passive:false});

      window.addEventListener('keyup',e=>{
        keys.delete(normalizeKey(e));
      });

      window.addEventListener('blur',()=>keys.clear());

      document.addEventListener('visibilitychange',()=>{
        if(document.hidden) keys.clear();
      });

      canvas.addEventListener('pointerdown',()=>canvas.focus());

      requestAnimationFrame(frame);
    })();
    </script>
    </body>
    </html>
    """

    components.html(game_html, height=750, scrolling=False)