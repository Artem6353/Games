/**
 * Gold Mining Clicker - Particle System
 * Handles visual effects for clicks, mining, and events
 */

const Particles = {
    canvas: null,
    ctx: null,
    particles: [],
    enabled: true,
    maxParticles: 200,
    
    init() {
        this.canvas = document.getElementById('particleCanvas');
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.resize();
        
        window.addEventListener('resize', () => this.resize());
        
        // Start animation loop
        requestAnimationFrame(() => this.animate());
    },
    
    resize() {
        if (!this.canvas) return;
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    },
    
    setEnabled(enabled) {
        this.enabled = enabled;
        if (!enabled) {
            this.particles = [];
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    },
    
    spawn(x, y, count = 10, options = {}) {
        if (!this.enabled || !this.ctx) return;
        
        const colors = options.colors || ['#ffd700', '#ffb347', '#ffec8b', '#ffffff'];
        const size = options.size || { min: 2, max: 6 };
        const velocity = options.velocity || { min: 2, max: 8 };
        
        for (let i = 0; i < Math.min(count, this.maxParticles); i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = Helpers.randomFloat(velocity.min, velocity.max);
            
            this.particles.push({
                x,
                y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed - 2,
                size: Helpers.randomFloat(size.min, size.max),
                color: colors[Math.floor(Math.random() * colors.length)],
                life: 1,
                decay: Helpers.randomFloat(0.015, 0.03),
                gravity: 0.15,
                rotation: Math.random() * Math.PI * 2,
                rotationSpeed: Helpers.randomFloat(-0.2, 0.2),
                shape: Math.random() > 0.5 ? 'circle' : 'square'
            });
        }
        
        // Limit total particles
        if (this.particles.length > this.maxParticles) {
            this.particles = this.particles.slice(-this.maxParticles);
        }
    },
    
    spawnGold(x, y) {
        this.spawn(x, y, 15, {
            colors: ['#ffd700', '#ffb347', '#ffec8b'],
            size: { min: 3, max: 8 },
            velocity: { min: 3, max: 10 }
        });
    },
    
    spawnSparkle(x, y) {
        this.spawn(x, y, 8, {
            colors: ['#ffffff', '#da70d6', '#4a9eff'],
            size: { min: 2, max: 4 },
            velocity: { min: 1, max: 4 }
        });
    },
    
    spawnExplosion(x, y) {
        this.spawn(x, y, 50, {
            colors: ['#ff6b6b', '#ffd700', '#ffa500', '#ffffff'],
            size: { min: 4, max: 12 },
            velocity: { min: 5, max: 15 }
        });
    },
    
    animate() {
        if (!this.ctx || !this.enabled) return;
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            
            // Update position
            p.x += p.vx;
            p.y += p.vy;
            p.vy += p.gravity;
            
            // Update life
            p.life -= p.decay;
            
            // Update rotation
            p.rotation += p.rotationSpeed;
            
            if (p.life <= 0) {
                this.particles.splice(i, 1);
                continue;
            }
            
            // Draw particle
            this.ctx.save();
            this.ctx.translate(p.x, p.y);
            this.ctx.rotate(p.rotation);
            this.ctx.globalAlpha = p.life;
            this.ctx.fillStyle = p.color;
            
            if (p.shape === 'circle') {
                this.ctx.beginPath();
                this.ctx.arc(0, 0, p.size, 0, Math.PI * 2);
                this.ctx.fill();
            } else {
                this.ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
            }
            
            this.ctx.restore();
        }
        
        requestAnimationFrame(() => this.animate());
    }
};

window.Particles = Particles;
