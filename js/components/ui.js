/**
 * Gold Mining Clicker - UI Components
 * Handles all user interface rendering and interactions
 */

const UI = {
    elements: {},
    
    init() {
        // Cache DOM elements
        this.elements = {
            goldAmount: document.getElementById('goldAmount'),
            gpsAmount: document.getElementById('gpsAmount'),
            clickPower: document.getElementById('clickPower'),
            globalMultiplier: document.getElementById('globalMultiplier'),
            totalMined: document.getElementById('totalMined'),
            totalClicks: document.getElementById('totalClicks'),
            playTime: document.getElementById('playTime'),
            upgradesCount: document.getElementById('upgradesCount'),
            mineralsFound: document.getElementById('mineralsFound'),
            eternityBars: document.getElementById('eternityBars'),
            prestigeBonus: document.getElementById('prestigeBonus'),
            achievementsList: document.getElementById('achievementsList'),
            eventContainer: document.getElementById('eventContainer'),
            mineButton: document.getElementById('mineButton'),
            toolsGrid: document.getElementById('toolsGrid'),
            minersGrid: document.getElementById('minersGrid'),
            engineersGrid: document.getElementById('engineersGrid'),
            buildingsGrid: document.getElementById('buildingsGrid'),
            researchTree: document.getElementById('researchTree'),
            comboDisplay: document.getElementById('comboDisplay'),
            comboCount: document.getElementById('comboCount'),
            notificationContainer: document.getElementById('notificationContainer'),
            saveIndicator: document.getElementById('saveIndicator'),
            saveText: document.getElementById('saveText')
        };
        
        this.initTabs();
        this.initToggles();
    },
    
    initTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;
                
                // Update buttons
                tabBtns.forEach(b => {
                    b.classList.remove('active');
                    b.setAttribute('aria-selected', 'false');
                });
                btn.classList.add('active');
                btn.setAttribute('aria-selected', 'true');
                
                // Update content
                tabContents.forEach(content => {
                    content.classList.remove('active');
                });
                document.getElementById(`${tabId}Tab`).classList.add('active');
            });
        });
    },
    
    initToggles() {
        const toggles = document.querySelectorAll('.toggle-switch[role="switch"]');
        
        toggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                toggle.classList.toggle('active');
                const isActive = toggle.classList.contains('active');
                toggle.setAttribute('aria-checked', isActive.toString());
            });
            
            // Keyboard support
            toggle.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggle.click();
                }
            });
        });
    },
    
    updateGold(amount) {
        if (this.elements.goldAmount) {
            this.elements.goldAmount.textContent = Calculator.formatNumber(amount);
        }
    },
    
    updateGPS(gps) {
        if (this.elements.gpsAmount) {
            this.elements.gpsAmount.textContent = Calculator.formatNumber(gps);
        }
    },
    
    updateClickPower(power) {
        if (this.elements.clickPower) {
            this.elements.clickPower.textContent = Calculator.formatNumber(power);
        }
    },
    
    updateGlobalMultiplier(mult) {
        if (this.elements.globalMultiplier) {
            this.elements.globalMultiplier.textContent = `x${mult.toFixed(2)}`;
        }
    },
    
    updateStats(stats) {
        if (this.elements.totalMined) {
            this.elements.totalMined.textContent = Calculator.formatNumber(stats.totalMined);
        }
        if (this.elements.totalClicks) {
            this.elements.totalClicks.textContent = Calculator.formatNumber(stats.totalClicks);
        }
        if (this.elements.playTime) {
            this.elements.playTime.textContent = Calculator.formatTime(stats.playTime * 1000);
        }
        if (this.elements.upgradesCount) {
            this.elements.upgradesCount.textContent = stats.upgradesPurchased;
        }
        if (this.elements.mineralsFound) {
            this.elements.mineralsFound.textContent = stats.mineralsFound;
        }
    },
    
    updatePrestige(count, bonus) {
        if (this.elements.eternityBars) {
            this.elements.eternityBars.textContent = count;
        }
        if (this.elements.prestigeBonus) {
            this.elements.prestigeBonus.textContent = `+${(bonus * 10).toFixed(0)}%`;
        }
    },
    
    showFloatingText(x, y, text, type = 'normal') {
        const element = document.createElement('div');
        element.className = `floating-text ${type}`;
        element.textContent = text;
        element.style.left = `${x}px`;
        element.style.top = `${y}px`;
        document.body.appendChild(element);
        
        setTimeout(() => element.remove(), 1000);
    },
    
    updateCombo(combo) {
        if (!this.elements.comboDisplay) return;
        
        if (combo.current > 1) {
            this.elements.comboDisplay.classList.add('active');
            this.elements.comboCount.textContent = `x${combo.current}`;
        } else {
            this.elements.comboDisplay.classList.remove('active');
        }
    },
    
    showNotification(message, type = 'info') {
        const icons = {
            success: '✅',
            warning: '⚠️',
            error: '❌',
            info: 'ℹ️'
        };
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <span class="notification-icon">${icons[type]}</span>
            <span class="notification-message">${message}</span>
        `;
        
        this.elements.notificationContainer.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideIn 0.3s ease reverse forwards';
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    },
    
    showSaveIndicator(saving) {
        if (!this.elements.saveIndicator) return;
        
        if (saving) {
            this.elements.saveIndicator.classList.add('saving');
            this.elements.saveText.textContent = 'Сохранение...';
        } else {
            this.elements.saveIndicator.classList.remove('saving');
            this.elements.saveText.textContent = 'Сохранено';
        }
    },
    
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    },
    
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    },
    
    renderUpgradeCard(item, level, canAfford, onClick) {
        const cost = Calculator.calculateCost(item.baseCost, level);
        const rarity = item.rarity || 'common';
        
        return `
            <div class="upgrade-card ${rarity} ${!canAfford ? 'disabled' : ''}" 
                 data-id="${item.id}" 
                 role="listitem"
                 tabindex="${canAfford ? '0' : '-1'}">
                <div class="upgrade-header">
                    <span class="upgrade-name">${item.name}</span>
                    <span class="upgrade-level">Ур. ${level}</span>
                </div>
                <p class="upgrade-description">${item.description}</p>
                <div class="upgrade-cost">
                    <span>💰</span>
                    <span>${Calculator.formatNumber(cost)}</span>
                </div>
                <div class="upgrade-bonus">
                    +${item.basePower || item.baseGPS} ${item.basePower ? 'к клику' : '/сек'}
                </div>
            </div>
        `;
    },
    
    renderResearchNode(tech, state) {
        const researched = state.research.includes(tech.id);
        const canAfford = state.gold >= tech.cost;
        const prereqsMet = Calculator.canResearch(state, tech.id);
        const locked = !prereqsMet && !researched;
        
        return `
            <div class="research-node ${researched ? 'researched' : ''} ${locked ? 'locked' : ''}" 
                 data-id="${tech.id}"
                 tabindex="${!locked && !researched ? '0' : '-1'}">
                <div class="research-icon">${tech.icon || '🔬'}</div>
                <div class="research-info">
                    <div class="research-name">${tech.name}</div>
                    <div class="research-desc">${tech.description}</div>
                    ${!researched ? `<div class="research-cost">💰 ${Calculator.formatNumber(tech.cost)}</div>` : ''}
                    ${tech.prerequisites.length > 0 ? `
                        <div class="research-prerequisites">Требует: ${tech.prerequisites.join(', ')}</div>
                    ` : ''}
                </div>
            </div>
        `;
    },
    
    renderAchievement(achievement, unlocked) {
        return `
            <div class="achievement-item ${unlocked ? 'unlocked' : ''}" role="listitem">
                <div class="achievement-icon">${achievement.icon}</div>
                <div class="achievement-info">
                    <div class="achievement-name">${achievement.name}</div>
                    <div class="achievement-desc">${achievement.description}</div>
                </div>
            </div>
        `;
    },
    
    renderEvent(event) {
        if (!event) {
            this.elements.eventContainer.innerHTML = '';
            return;
        }
        
        this.elements.eventContainer.innerHTML = `
            <div class="event-banner">
                <div class="event-name">${event.icon} ${event.name}</div>
                <div class="event-timer">${event.description}</div>
            </div>
        `;
    },
    
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('hidden');
            setTimeout(() => overlay.remove(), 500);
        }
    },
    
    showMineralPopup(mineral) {
        const popup = document.getElementById('mineralPopup');
        const icon = document.getElementById('mineralIcon');
        const name = document.getElementById('mineralName');
        const bonus = document.getElementById('mineralBonus');
        
        if (popup && icon && name && bonus) {
            icon.textContent = mineral.icon;
            name.textContent = mineral.name;
            bonus.textContent = `+${Calculator.formatNumber(mineral.bonus)} золота`;
            popup.classList.add('active');
        }
    },
    
    hideMineralPopup() {
        const popup = document.getElementById('mineralPopup');
        if (popup) {
            popup.classList.remove('active');
        }
    }
};

window.UI = UI;
