with open('/home/madge/Bản tải về/Virtual-Assistantpop/web/pop-landing/index.html', 'r') as f:
    content = f.read()

# 1. Replace nav logo with a simple circle
old_nav_logo = '''<div class="brand-logo">
                    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="2" y="2" width="32" height="32" rx="8" fill="url(#logoGrad)" fill-opacity="0.15"/>
                        <rect x="2" y="2" width="32" height="32" rx="8" stroke="url(#logoGrad)" stroke-width="2"/>
                        <path d="M10 12H14L18 24L22 12H26" stroke="url(#logoGrad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <circle cx="26" cy="24" r="2" fill="url(#logoGrad)"/>
                        <defs>
                            <linearGradient id="logoGrad" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                                <stop stop-color="#00FFAA"/>
                                <stop offset="1" stop-color="#00CCFF"/>
                            </linearGradient>
                        </defs>
                    </svg>
                </div>'''

new_nav_logo = '''<div class="brand-logo">
                    <div class="logo-circle-nav"></div>
                </div>'''

content = content.replace(old_nav_logo, new_nav_logo)

# 2. Replace hero logo with halo circle
old_hero_logo = '''<div class="hero-core">
                        <div class="premium-logo-container">
                            <svg width="120" height="120" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <defs>
                                    <linearGradient id="heroGrad" x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
                                        <stop stop-color="#00FFAA"/>
                                        <stop offset="1" stop-color="#00CCFF"/>
                                    </linearGradient>
                                </defs>
                                <!-- Abstract Workflow Symbol: Orchestration Loop -->
                                <path d="M50 20C33.4315 20 20 33.4315 20 50C20 66.5685 33.4315 80 50 80C66.5685 80 80 66.5685 80 50C80 33.4315 66.5685 20 50 20Z" stroke="url(#heroGrad)" stroke-width="3" stroke-linecap="round"/>
                                <path d="M50 20V10M50 80V90M20 50H10M80 50H90" stroke="url(#heroGrad)" stroke-width="3" stroke-linecap="round"/>
                                <path d="M30 30L50 50L70 30M30 70L50 50L70 70" stroke="url(#heroGrad)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                                <circle cx="50" cy="20" r="4" fill="url(#heroGrad)"/>
                                <circle cx="80" cy="50" r="4" fill="url(#heroGrad)"/>
                                <circle cx="50" cy="80" r="4" fill="url(#heroGrad)"/>
                                <circle cx="20" cy="50" r="4" fill="url(#heroGrad)"/>
                                <circle cx="50" cy="50" r="8" fill="url(#heroGrad)"/>
                            </svg>
                        </div>
                    </div>'''

new_hero_logo = '''<div class="hero-core">
                        <div class="halo-logo">
                            <div class="halo-ring halo-ring-1"></div>
                            <div class="halo-ring halo-ring-2"></div>
                            <div class="halo-ring halo-ring-3"></div>
                            <div class="halo-core">
                                <div class="halo-inner-ring"></div>
                                <div class="halo-center-dot"></div>
                            </div>
                        </div>
                    </div>'''

content = content.replace(old_hero_logo, new_hero_logo)

with open('/home/madge/Bản tải về/Virtual-Assistantpop/web/pop-landing/index.html', 'w') as f:
    f.write(content)

print('Done! Logos replaced with halo circles.')
