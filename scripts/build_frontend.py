"""Frontend Builder for Enterprise Global Lead Gen Platform."""

import re
from pathlib import Path

INDEX_PATH = Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/src/web/index.html")

# Read existing index.html
with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Header Navigation
old_nav = """    <!-- Navigation Tabs -->
    <nav class="nav-tabs">
      <a href="javascript:void(0)" onclick="navigateTo('home')" id="tab-home" class="nav-tab-link active">HOME</a>
      <a href="javascript:void(0)" onclick="navigateTo('about')" id="tab-about" class="nav-tab-link">ABOUT US</a>
      <a href="javascript:void(0)" onclick="navigateTo('services')" id="tab-services" class="nav-tab-link">SERVICES</a>
      <a href="javascript:void(0)" onclick="navigateTo('mission-control')" id="tab-mission-control" class="nav-tab-link">AUTONOMOUS OS</a>
      <a href="javascript:void(0)" onclick="navigateTo('pipeline')" id="tab-pipeline" class="nav-tab-link">CLIENT PIPELINE</a>
      <a href="javascript:void(0)" onclick="navigateTo('contact')" id="tab-contact" class="nav-tab-link">CONTACT US</a>
    </nav>"""

new_nav = """    <!-- Primary Enterprise Navigation Tabs -->
    <nav class="nav-tabs">
      <a href="javascript:void(0)" onclick="navigateTo('explorer')" id="tab-explorer" class="nav-tab-link active">🌐 GLOBAL DIRECTORY</a>
      <a href="javascript:void(0)" onclick="navigateTo('pipelines')" id="tab-pipelines" class="nav-tab-link">⚡ INGESTION PIPELINES</a>
      <a href="javascript:void(0)" onclick="navigateTo('compliance')" id="tab-compliance" class="nav-tab-link">🛡️ COMPLIANCE & DNC</a>
      <a href="javascript:void(0)" onclick="navigateTo('api-docs')" id="tab-api-docs" class="nav-tab-link">🔌 DEVELOPER API</a>
      <a href="javascript:void(0)" onclick="navigateTo('home')" id="tab-home" class="nav-tab-link">🏢 AGENCY PORTAL</a>
    </nav>"""

if old_nav in content:
    content = content.replace(old_nav, new_nav)
else:
    print("Warning: old_nav not matched exactly, replacing via regex")
    content = re.sub(r'<nav class="nav-tabs">.*?</nav>', new_nav.strip(), content, flags=re.DOTALL)

# 2. Update Mobile Nav Panel
old_mobile_nav = """    <!-- Mobile Nav Panel -->
    <div id="mobile-nav-panel" class="mobile-nav-panel">
      <a href="javascript:void(0)" onclick="navigateTo('home'); toggleMobileNav()" class="nav-tab-link">HOME</a>
      <a href="javascript:void(0)" onclick="navigateTo('about'); toggleMobileNav()" class="nav-tab-link">ABOUT US</a>
      <a href="javascript:void(0)" onclick="navigateTo('services'); toggleMobileNav()" class="nav-tab-link">SERVICES</a>
      <a href="javascript:void(0)" onclick="navigateTo('mission-control'); toggleMobileNav()" class="nav-tab-link">AUTONOMOUS OS</a>
      <a href="javascript:void(0)" onclick="navigateTo('pipeline'); toggleMobileNav()" class="nav-tab-link">CLIENT PIPELINE</a>
      <a href="javascript:void(0)" onclick="navigateTo('contact'); toggleMobileNav()" class="nav-tab-link">CONTACT US</a>"""

new_mobile_nav = """    <!-- Mobile Nav Panel -->
    <div id="mobile-nav-panel" class="mobile-nav-panel">
      <a href="javascript:void(0)" onclick="navigateTo('explorer'); toggleMobileNav()" class="nav-tab-link">🌐 GLOBAL DIRECTORY</a>
      <a href="javascript:void(0)" onclick="navigateTo('pipelines'); toggleMobileNav()" class="nav-tab-link">⚡ INGESTION PIPELINES</a>
      <a href="javascript:void(0)" onclick="navigateTo('compliance'); toggleMobileNav()" class="nav-tab-link">🛡️ COMPLIANCE & DNC</a>
      <a href="javascript:void(0)" onclick="navigateTo('api-docs'); toggleMobileNav()" class="nav-tab-link">🔌 DEVELOPER API</a>
      <a href="javascript:void(0)" onclick="navigateTo('home'); toggleMobileNav()" class="nav-tab-link">🏢 AGENCY PORTAL</a>
      <a href="javascript:void(0)" onclick="navigateTo('about'); toggleMobileNav()" class="nav-tab-link" style="font-size: 11px; opacity: 0.7;">— ABOUT US</a>
      <a href="javascript:void(0)" onclick="navigateTo('services'); toggleMobileNav()" class="nav-tab-link" style="font-size: 11px; opacity: 0.7;">— SERVICES</a>
      <a href="javascript:void(0)" onclick="navigateTo('mission-control'); toggleMobileNav()" class="nav-tab-link" style="font-size: 11px; opacity: 0.7;">— AUTONOMOUS OS</a>
      <a href="javascript:void(0)" onclick="navigateTo('contact'); toggleMobileNav()" class="nav-tab-link" style="font-size: 11px; opacity: 0.7;">— CONTACT US</a>"""

if old_mobile_nav in content:
    content = content.replace(old_mobile_nav, new_mobile_nav)
else:
    content = re.sub(r'<div id="mobile-nav-panel" class="mobile-nav-panel">.*?(?=<button onclick="openAuthModal\(\))', new_mobile_nav + '\n      ', content, flags=re.DOTALL)

# Write modified file
with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Navigation replaced successfully.")
