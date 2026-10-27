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

st.title("🎮 2인용 탱크 전쟁")
st.caption("두 명이 함께 싸우는 2D 탱크 배틀!")

if "game_started" not in st.session_state:
    st.session_state.game_started = False

if not st.session_state.game_started:
    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#182d3b,#263d32);
        border:2px solid #5d8d73;
        border-radius:18px;
        padding:35px 20px;
        text-align:center;
        margin:15px 0;
    ">
        <div style="font-size:70px;">🚜 💥 🚜</div>
        <h1 style="color:#b5ffb8;">TANK WAR</h1>
        <p style="font-size:18px;">
            넓은 전장에서 상대 탱크를 공격하라!
        </p>
        <p>작은 탱크 · 넓은 맵 · 장애물 · 실시간 전투</p>
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
        "탱크는 가만히 있으면 자동으로 회전해. "
        "전진 키를 누르고 있는 동안에는 회전을 멈추고 이동해!"
    )

if st.button("🚀 게임 시작", type="primary"):
    st.session_state.game_started = True
    st.rerun()
else:
    st.markdown("""
    **🟢 1P:** W 이동 / SPACE 발사
    &nbsp;&nbsp; | &nbsp;&nbsp;
    **🔴 2P:** O 이동 / P 발사
    &nbsp;&nbsp; | &nbsp;&nbsp;
    **발사 쿨타임:** 2초
    """)

    if st.button("↩️ 시작 화면으로"):
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
        padding: 8px 12px;
        background: #1c2c32;
        border: 1px solid #42604d;
        border-radius: 10px 10px 0 0;
        font-weight: bold;
        font-size: 13px;
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
        font-size: 12px;
        color: #c9d8cc;
        text-align: center;
        padding: 8px;
        line-height: 1.7;
      }
      #restart {
        margin-top: 6px;
        padding: 8px 16px;
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
        <span style="color:#69ff8c">🟢 P1 <span id="hp1">3</span> HP</span>
        <span id="status">TANK WAR</span>
        <span style="color:#ff7777">P2 <span id="hp2">3</span> HP 🔴</span>
      </div>
      <canvas id="game" width="1000" height="650" tabindex="0"></canvas>
      <div id="help">
        W: 초록 탱크 전진 · SPACE: 발사
        &nbsp; | &nbsp;
        O: 빨간 탱크 전진 · P: 발사<br>
        이동 키를 놓으면 자동 회전 · 포탄은 2초마다 발사 가능
        <br><button id="restart" type="button">🔄 다시 시작</button>
      </div>

    <script>
    (() => {
      const canvas = document.getElementById('game');
      const ctx = canvas.getContext('2d');
      const W = 1000, H = 650;
      const MW = 2200, MH = 1500;
      const keys = new Set();

      let running = true;
      let last = performance.now();
      let now = 0;
      let bullets = [];
      let particles = [];
      let winner = '';
      let audio = null;

      const obstacles = [];

      // 넓은 맵 곳곳에 장애물 배치
      function addRect(x, y, w, h, type='rock') {
        obstacles.push({x,y,w,h,type});
      }

      // 맵 가장자리 벽
      addRect(0,0,MW,35,'wall');
      addRect(0,MH-35,MW,35,'wall');
      addRect(0,0,35,MH,'wall');
      addRect(MW-35,0,35,MH,'wall');

      // 중앙 장애물과 엄폐물
      [
        [450,250,150,60], [820,160,65,180],
        [1180,280,190,65], [1570,160,75,200],
        [350,600,70,180], [700,750,180,65],
        [1100,580,70,200], [1500,720,200,65],
        [1800,520,70,160], [250,1000,180,65],
        [650,1150,65,150], [1000,1000,190,65],
        [1400,1120,70,180], [1770,1000,180,65],
        [950,420,65,65], [1300,880,65,65],
        [500,850,65,65], [1650,400,65,65]
      ].forEach(a => addRect(...a));

      const tanks = [
        {
          x: 150, y: 150, angle: 0,
          color: '#42e66e', dark: '#167b37',
          key: 'w', fire: ' ', hp: 3, lastShot: -2000
        },
        {
          x: 2050, y: 1350, angle: Math.PI,
          color: '#ff5656', dark: '#9b2525',
          key: 'o', fire: 'p', hp: 3, lastShot: -2000
        }
      ];

      function sound() {
        try {
          audio = audio || new (
            window.AudioContext || window.webkitAudioContext
          )();
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

      function blocked(x,y,r) {
        if (x < r || y < r || x > MW-r || y > MH-r) {
          return true;
        }
        return obstacles.some(o => circleRect(x,y,r,o));
      }

      function tankBlocked(t, x, y) {
        if (blocked(x,y,15)) return true;
        return tanks.some(other =>
          other !== t &&
          Math.hypot(other.x-x, other.y-y) < 32
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
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(t===tanks[0]?'P1':'P2',t.x,t.y-23);

        // 체력 표시
        ctx.fillStyle = '#1b1b1b';
        ctx.fillRect(t.x-17,t.y+19,34,5);
        ctx.fillStyle = t.color;
        ctx.fillRect(t.x-17,t.y+19,34*Math.max(0,t.hp)/3,5);
      }

      function drawObstacle(o) {
        if(o.type==='wall') {
          ctx.fillStyle='#59665a';
          ctx.fillRect(o.x,o.y,o.w,o.h);
          ctx.strokeStyle='#829184';
          ctx.lineWidth=2;
          ctx.strokeRect(o.x,o.y,o.w,o.h);
          return;
        }

        ctx.fillStyle='#25342b';
        ctx.fillRect(o.x+5,o.y+6,o.w,o.h);

        ctx.fillStyle='#677b63';
        ctx.fillRect(o.x,o.y,o.w,o.h);

        ctx.fillStyle='#83977b';
        ctx.fillRect(o.x+5,o.y+5,Math.max(0,o.w-10),5);

        ctx.strokeStyle='#344a38';
        ctx.lineWidth=3;
        ctx.strokeRect(o.x,o.y,o.w,o.h);
      }

      function update(dt) {
        if(!running) return;

        const speed = 3.3 * dt;
        const rotationSpeed = 0.0025 * dt;

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

          if(blocked(b.x,b.y,4)) b.life=0;

          tanks.forEach((t,i) => {
            if(i!==b.owner && t.hp>0 &&
               Math.hypot(t.x-b.x,t.y-b.y)<17) {
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
                winner = i===0 ? 'P2 승리!' : 'P1 승리!';
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
        // 플레이어 1을 중심으로 카메라를 이동시켜 조작 중 화면이 튀지 않게 함.
        // 두 탱크가 맵 양 끝에 있어도 시작 직후 각 탱크를 찾기 쉽도록 P1 기준.
        const focusX=tanks[0].x;
        const focusY=tanks[0].y;
        const camX=Math.max(0,Math.min(MW-W,focusX-W/2));
        const camY=Math.max(0,Math.min(MH-H,focusY-H/2));

        ctx.clearRect(0,0,W,H);
        ctx.save();
        ctx.translate(-camX,-camY);

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
          winner || `P1 발사 ${cd1.toFixed(1)}s | P2 발사 ${cd2.toFixed(1)}s`;

        if(!running) {
          ctx.fillStyle='rgba(0,0,0,0.72)';
          ctx.fillRect(0,0,W,H);
          ctx.textAlign='center';
          ctx.fillStyle='#ffffff';
          ctx.font='bold 44px Arial';
          ctx.fillText(winner,W/2,H/2-12);
          ctx.font='20px Arial';
          ctx.fillText('페이지를 새로고침하면 다시 시작할 수 있어!',W/2,H/2+32);
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
            // 버튼을 꾹 누르는 동안 연속 발사하되 쿨타임 적용
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

    components.html(game_html, height=740, scrolling=False)

st.caption("Tank War · Python + Streamlit + HTML Canvas")