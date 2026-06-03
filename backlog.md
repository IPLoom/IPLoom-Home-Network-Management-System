# IPLoom Backlog

This document tracks the planned features and improvements for the IPLoom Home Network Management System.

---

## 🚀 Active Roadmap (Prioritized)

### 1. 🔒 OpenWrt Block/Unblock & Policy Engine  *(Completed)*
**Status:** Completed ✅
- Added centralized `policy.py` state resolver (Manual vs Schedule vs Quota).
- Implemented OpenWrt firewall enforcement (DROP rules + conntrack flushing).
- Integrated "Administrator Override" (Manual Unblock) with highest priority.
- UI: Block/Unblock toggles and Quota Manager are fully functional.

### 2. 🔔 New Device Alert — WebSocket Push + TopBar Badge  *(Completed)*
**Status:** Completed ✅
- Wired `new_device` task events to the existing WebSocket broadcast.
- Added a **dedicated "New Devices" badge** and popover in the TopBar.
- Implemented `localStorage` persistence for badge dismissal.
- Added `new_only` filter to the devices API.


### 3. 🛡️ Security Center — Tab inside Analytics/Insights  *(Medium Priority)*
**Status:** Not started. Untrusted device styling exists in DeviceList but no dedicated view.
- Add a **"Security" tab** inside the existing Analytics view (alongside Overview, Traffic, etc.)
- Sections:
  - **Untrusted Devices** — All `is_trusted = false` devices with one-click trust action
  - **Risky Open Ports** — Devices exposing ports 23 (Telnet), 21 (FTP), 135, 3389 (RDP), etc.
  - **New Devices (7 days)** — Recently discovered, not yet classified
  - **Blocked Devices** — Devices currently blocked via OpenWrt (requires #1)
- Backend: New `/api/v1/analytics/security-summary` endpoint aggregating the above

### 4. 📡 WLAN Association Details from OpenWrt  *(Medium Priority)*
**Status:** OpenWrt integration is live but only fetches ARP/DHCP data.
- Fetch `iwinfo` data via OpenWrt ubus: Wi-Fi band (2.4/5/6GHz), RSSI signal strength, TX rate per device
- Store on device: `wifi_band`, `wifi_rssi`, `wifi_tx_rate` fields (attributes JSON or dedicated columns)
- Display in DeviceDetails Network Insights Bar: signal strength indicator, band badge
- Display signal strength column in DeviceList (optional, toggleable)

---

## 📱 Mobile Application (Flutter)
- [ ] **Data Quota Parity**: Bring consumption progress bars and "Manual Unblock" override to the mobile dashboard.
- [ ] **Schedule Management**: Implement the touch-optimized heatmap for access windows.
- [ ] **Functional Quick Actions**: Implement "Scan Now" and "Security Audit" triggers from the mobile UI.
- [ ] **Dynamic Integration Status**: Sync AdGuard, OpenWrt, and MQTT status badges with real-time backend state.

## 🎨 UI Modernization (Vuetify Migration)
- [ ] **Phase 1**: Setup Vuetify 3 + Vite Plugin and migrate Core Layout (Nav & TopBar).
- [ ] **Phase 2**: Migrate Dashboard (Stats Cards & Device Table).
- [ ] **Phase 3**: Migrate Device Details (Tabs & Quota Manager).
- [ ] **Phase 4**: Standardize Theme (Glassmorphism + Dark Mode).

## 📈 Future Enhancements
- [ ] **Network Topology Map**: Visual graph showing physical connections (Port 1, 2, etc.) and Wi-Fi Mesh relationships.
- [ ] **Dynamic DNS (DDNS) Status**: Monitor and update public-facing IP status for remote access.
- [ ] **Premium Theme Engine**: Allow users to choose between various glassmorphism accents (Indigo, Emerald, Rose).
- [ ] **Enrich MQTT Home Assistant Sensors**: Expand published MQTT data attributes for HA (`deco_node` satellite, Wi-Fi band, RSSI, OpenWrt speed rates, quota limits, blocking schedules) instead of just the `online`/`offline` status tracker.
