with open('/home/madge/Bản tải về/Virtual-Assistantpop/web/pop-landing/index.html', 'r') as f:
    content = f.read()

# Find and replace nav logo - use position-based replacement
pos = content.find('<div class="brand-logo">')
if pos != -1:
    # Find the end of this brand-logo div
    end_pos = content.find('</div>', pos)
    end_pos = content.find('</div>', end_pos + 1)  # Find second closing div
    
    old_nav = content[pos:end_pos + 6]
    new_nav = '''<div class="brand-logo">
 <div class="logo-circle-nav">
 <div class="nav-halo-ring"></div>
 <div class="nav-halo-ring nav-halo-ring-2"></div>
 <div class="nav-halo-core"></div>
 </div>
 </div>'''
    
    content = content.replace(old_nav, new_nav)
    with open('/home/madge/Bản tải về/Virtual-Assistantpop/web/pop-landing/index.html', 'w') as f:
        f.write(content)
    print('Nav logo updated!')
    print('Old:', repr(old_nav[:150]))
else:
    print('brand-logo not found')
