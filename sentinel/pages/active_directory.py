import streamlit as st

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background: #050d1a !important; }
    [data-testid="stSidebar"]          { background: #0d0d0d !important; }
    [data-testid="stSidebarContent"]   { background: #0d0d0d !important; }

    .page-header {
        font-size: 1.9rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00d4ff 0%, #ffffff 55%, #00d4ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 0 14px rgba(0,212,255,0.4));
        letter-spacing: 0.1em;
        margin-bottom: 0.15rem;
    }
    .page-sub {
        color: #4d7a8a;
        font-size: 0.88rem;
        letter-spacing: 0.05em;
        margin-bottom: 1.5rem;
    }

    /* Section heading inside a tab */
    .s-head {
        color: #00d4ff;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(0,212,255,0.15);
        padding-bottom: 0.3rem;
        margin-bottom: 0.6rem;
        margin-top: 1.2rem;
    }
    .s-head:first-child { margin-top: 0; }

    /* Body text */
    .s-body {
        color: #8ab0c4;
        font-size: 0.88rem;
        line-height: 1.75;
        margin: 0 0 0.5rem;
    }

    /* Bullet item */
    .s-li {
        color: #8ab0c4;
        font-size: 0.87rem;
        line-height: 1.65;
        padding: 0.18rem 0 0.18rem 1rem;
        position: relative;
    }
    .s-li::before { content:"›"; color:#00d4ff; position:absolute; left:0; font-weight:700; }

    /* Command block */
    .cmd {
        background: rgba(0,0,0,0.5);
        border-left: 3px solid #00d4ff;
        border-radius: 0 8px 8px 0;
        padding: 0.7rem 1.1rem;
        font-family: monospace;
        font-size: 0.83rem;
        color: #55ddf0;
        margin: 0.4rem 0 0.25rem;
        line-height: 1.7;
        white-space: pre-wrap;
        word-break: break-all;
    }

    /* Step card */
    .step-card {
        background: rgba(0,15,30,0.8);
        border: 1px solid rgba(0,212,255,0.12);
        border-radius: 12px;
        padding: 1.1rem 1.4rem 1.2rem;
        margin-bottom: 1rem;
    }
    .step-num {
        display: inline-block;
        background: #00d4ff;
        color: #050d1a;
        font-size: 0.7rem;
        font-weight: 900;
        letter-spacing: 0.1em;
        border-radius: 4px;
        padding: 0.1rem 0.55rem;
        margin-bottom: 0.5rem;
    }
    .step-title {
        color: #ffffff;
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }
    .step-body {
        color: #8ab0c4;
        font-size: 0.86rem;
        line-height: 1.7;
    }

    /* Concept card (for "What is AD") */
    .concept-card {
        background: rgba(0,20,40,0.85);
        border: 1px solid rgba(0,212,255,0.18);
        border-top: 2px solid var(--c, #00d4ff);
        border-radius: 12px;
        padding: 1.1rem 1.2rem;
        height: 100%;
    }
    .concept-icon { font-size: 1.8rem; margin-bottom: 0.4rem; }
    .concept-name { color:#ffffff; font-size:0.88rem; font-weight:700; margin-bottom:0.3rem; }
    .concept-desc { color:#6699aa; font-size:0.81rem; line-height:1.6; }

    /* Warning / note boxes */
    .warn-box {
        background: rgba(249,115,22,0.07);
        border: 1px solid rgba(249,115,22,0.3);
        border-radius: 8px;
        padding: 0.65rem 1rem;
        color: #f97316;
        font-size: 0.84rem;
        line-height: 1.6;
        margin: 0.5rem 0;
    }
    .note-box {
        background: rgba(0,212,255,0.06);
        border: 1px solid rgba(0,212,255,0.2);
        border-radius: 8px;
        padding: 0.65rem 1rem;
        color: #55ddf0;
        font-size: 0.84rem;
        line-height: 1.6;
        margin: 0.5rem 0;
    }

    /* Network diagram */
    .net-diagram {
        background: rgba(0,10,22,0.9);
        border: 1px solid rgba(0,212,255,0.15);
        border-radius: 14px;
        padding: 2rem;
        font-family: monospace;
        font-size: 0.85rem;
        color: #8ab0c4;
        line-height: 2;
        text-align: center;
    }
    .net-internet { color:#f97316; font-weight:700; font-size:1rem; }
    .net-pi       { color:#00d4ff; font-weight:700; }
    .net-dc       { color:#4ade80; font-weight:700; }
    .net-client   { color:#a855f7; font-weight:700; }
    .net-line     { color:#334455; }

    /* Role badge */
    .role-badge {
        display:inline-block;
        border-radius:5px;
        padding:0.08rem 0.5rem;
        font-size:0.68rem;
        font-weight:700;
        letter-spacing:0.08em;
        margin-left:0.4rem;
        vertical-align:middle;
    }
    .rb-pi     { background:rgba(0,212,255,0.12); color:#00d4ff; border:1px solid rgba(0,212,255,0.3); }
    .rb-dc     { background:rgba(74,222,128,0.1);  color:#4ade80; border:1px solid rgba(74,222,128,0.3); }
    .rb-client { background:rgba(168,85,247,0.1);  color:#a855f7; border:1px solid rgba(168,85,247,0.3); }

    .stTabs [data-baseweb="tab"] { font-weight:600; letter-spacing:0.04em; }
    .block-container { padding-top: 2rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="page-header">🏢 Active Directory Lab</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">Build a real enterprise-grade login environment using 100% free software — Samba 4 + Raspberry Pi</div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🏢 What is AD", "🗺 Network Map", "🖥 AD Setup", "🛡 Pi Firewall", "🔗 Join & Use"]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — WHAT IS ACTIVE DIRECTORY
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown(
        """
        <div class="s-head">What is Active Directory?</div>
        <div class="s-body">
            Active Directory (AD) is Microsoft's centralized directory service that controls who can access
            what on a network. Instead of every computer managing its own list of usernames and passwords,
            AD puts one server in charge — the <b style="color:#4ade80;">Domain Controller (DC)</b> — and every
            machine on the network trusts it. When you log in, your PC asks the DC "is this person allowed in?"
            and the DC either grants or denies access.
        </div>
        <div class="s-body">
            It is the backbone of almost every corporate Windows environment on the planet. When a company
            has 500 employees and needs to make sure only HR can open HR files, only IT can install software,
            and everyone's password resets in one place — that is Active Directory doing its job.
        </div>

        <div class="s-head">The Four Core Technologies</div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    c1.markdown(
        """<div class="concept-card" style="--c:#00d4ff;">
            <div class="concept-icon">🔑</div>
            <div class="concept-name">Kerberos</div>
            <div class="concept-desc">The authentication protocol. When you type your password, Kerberos
            issues a "ticket" — a cryptographic token you show to every service instead of typing your
            password again. Single sign-on (SSO) is built on this. No password ever travels across the
            network in plaintext.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    c2.markdown(
        """<div class="concept-card" style="--c:#4ade80;">
            <div class="concept-icon">📋</div>
            <div class="concept-name">LDAP</div>
            <div class="concept-desc">The directory protocol. LDAP (Lightweight Directory Access Protocol)
            is how applications query AD — "give me all users in the Finance group," "what groups does
            Alice belong to?" It's a structured database of every user, computer, and group on the
            domain, accessible in milliseconds.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    c3.markdown(
        """<div class="concept-card" style="--c:#a855f7;">
            <div class="concept-icon">🌐</div>
            <div class="concept-name">DNS</div>
            <div class="concept-desc">AD is completely DNS-dependent. Every service in the domain
            registers itself in DNS so that clients can find the DC, file shares, printers, and
            more by name. Your domain controller IS your DNS server — without it pointing right,
            nothing works. This is the #1 reason AD setups fail.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    c4.markdown(
        """<div class="concept-card" style="--c:#f97316;">
            <div class="concept-icon">⚙️</div>
            <div class="concept-name">Group Policy</div>
            <div class="concept-desc">The enforcement layer. Group Policy Objects (GPOs) let you push
            settings to every machine at once — disable USB drives, force a screensaver lock, require
            BitLocker encryption, set wallpapers, restrict which applications users can run. One change
            on the DC, every computer in the domain applies it at next login.</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <br>
        <div class="s-head">How Login Actually Works (Step by Step)</div>
        <div class="s-li">1. You type your username and password at the Windows login screen.</div>
        <div class="s-li">2. Your PC sends an <b>AS-REQ</b> (Authentication Service Request) to the DC, encrypted with a hash of your password.</div>
        <div class="s-li">3. The DC's Key Distribution Center (KDC) decrypts it, verifies your credentials, and issues a <b>Ticket Granting Ticket (TGT)</b> — valid for 10 hours by default.</div>
        <div class="s-li">4. Every time you open a file share, a printer, or a web app, your PC silently shows that TGT to get a <b>Service Ticket</b> for that specific resource.</div>
        <div class="s-li">5. The resource accepts the service ticket without ever asking for your password again. That is what SSO feels like from a user's perspective.</div>

        <br>
        <div class="s-head">Why Samba 4 Instead of Windows Server?</div>
        <div class="s-body">
            Windows Server costs hundreds of dollars per license. <b style="color:#00d4ff;">Samba 4</b> is a free,
            open-source implementation of the same AD protocols — same Kerberos, same LDAP, same DNS,
            same Group Policy compatibility. Windows machines cannot tell the difference. They domain-join
            and authenticate against Samba 4 exactly the same way they would against a Microsoft DC.
            It runs on Ubuntu Linux, which is also free. This entire lab costs $0 in software.
        </div>

        <div class="s-head">Why Companies Care About This</div>
        <div class="s-li">Every Fortune 500 company runs Active Directory or Azure AD (cloud AD). Knowing AD is a baseline expectation for any IT, sysadmin, or security role.</div>
        <div class="s-li">Active Directory is one of the most targeted systems in ransomware attacks. Once attackers gain Domain Admin, they own every machine in the organization.</div>
        <div class="s-li">BloodHound, a popular red team tool, maps attack paths through AD permissions. Understanding AD structure is required to both run it and defend against it.</div>
        <div class="s-li">Penetration testers charge thousands of dollars per engagement specifically to test AD configurations for privilege escalation paths, Kerberoasting, and Pass-the-Hash attacks.</div>
        """,
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — NETWORK MAP
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(
        """
        <div class="s-head">Your Home Lab Topology</div>
        <div class="s-body">
            This is the physical and logical layout of your lab. The Raspberry Pi sits between
            your home router and the rest of the lab, acting as a firewall and DNS filter.
            All lab machines talk through the Pi to reach the internet.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="net-diagram">
            <span class="net-internet">[ INTERNET ]</span><br>
            <span class="net-line">│</span><br>
            <span class="net-line">[ Home Router / ISP Modem ]</span><br>
            <span class="net-line">│</span><br>
            <span class="net-pi">[ Raspberry Pi — Firewall + Pi-hole ]</span><br>
            <span style="color:#334455; font-size:0.78rem;">eth0 = WAN → receives IP from home router (DHCP)<br>
            eth1 = LAN → 192.168.50.1 (gateway for the entire lab)<br>
            iptables does NAT · Pi-hole filters DNS</span><br>
            <span class="net-line">│</span><br>
            <span class="net-line">[ Network Switch or spare router ports ]</span><br>
            <span class="net-line">├──────────────────┬──────────────────┐</span><br>
            <span class="net-dc">[ DC1 · Spare PC ]</span>
            &nbsp;&nbsp;&nbsp;&nbsp;
            <span class="net-client">[ Windows Client 1 ]</span>
            &nbsp;&nbsp;&nbsp;&nbsp;
            <span class="net-client">[ Windows Client 2 ]</span><br>
            <span style="color:#334455; font-size:0.77rem;">
            192.168.50.10&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            192.168.50.20&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            192.168.50.21</span><br>
            <span style="color:#334455; font-size:0.77rem;">
            Ubuntu Server + Samba 4&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;SENTINEL\\alice&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;SENTINEL\\bob</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    col_a.markdown(
        """<div class="concept-card" style="--c:#00d4ff;">
            <div class="concept-name">🛡 Raspberry Pi <span class="role-badge rb-pi">FIREWALL</span></div>
            <div class="concept-desc"><b>IP:</b> 192.168.50.1 (LAN)<br>
            <b>Role:</b> Routes and filters all traffic between the lab and the internet.<br>
            Pi-hole blocks malware domains and ads at the DNS level for every device in the lab.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    col_b.markdown(
        """<div class="concept-card" style="--c:#4ade80;">
            <div class="concept-name">🖥 Spare PC <span class="role-badge rb-dc">DOMAIN CONTROLLER</span></div>
            <div class="concept-desc"><b>Hostname:</b> DC1.SENTINEL.LOCAL<br>
            <b>IP:</b> 192.168.50.10 (static)<br>
            <b>Role:</b> Runs Samba 4 AD DC. Handles all authentication, DNS for .LOCAL, LDAP queries, and Group Policy distribution.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    col_c.markdown(
        """<div class="concept-card" style="--c:#a855f7;">
            <div class="concept-name">💻 Windows PCs <span class="role-badge rb-client">CLIENTS</span></div>
            <div class="concept-desc"><b>IPs:</b> 192.168.50.20+<br>
            <b>Role:</b> Domain-joined Windows machines. Users log in with domain accounts (SENTINEL\\alice). Group Policy applies automatically.</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <br>
        <div class="s-head">IP Address Plan</div>
        """,
        unsafe_allow_html=True,
    )

    st.table(
        {
            "Device":           ["Raspberry Pi (LAN)", "Spare PC (DC1)", "Windows Client 1", "Windows Client 2", "Any other device"],
            "IP Address":       ["192.168.50.1",       "192.168.50.10",  "192.168.50.20",    "192.168.50.21",    "192.168.50.30+"],
            "Set By":           ["Static (manual)",    "Static (manual)", "Static or DHCP",  "Static or DHCP",   "DHCP"],
            "DNS Points To":    ["—",                  "127.0.0.1",       "192.168.50.10",   "192.168.50.10",    "192.168.50.1 (Pi-hole)"],
        }
    )

    st.markdown(
        """
        <div class="note-box">
        The domain controller (DC1) must have a <b>static IP</b> and must point its own DNS at itself (127.0.0.1).
        Client machines must point their DNS at the DC (192.168.50.10) — not at the Pi or your home router — or domain joining will fail.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AD SETUP
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown(
        """
        <div class="s-head">Prerequisites</div>
        <div class="s-li">A spare PC or laptop (any hardware from the last 10 years works — even 2 GB RAM is enough)</div>
        <div class="s-li">Ubuntu Server 22.04 LTS installed — download free at ubuntu.com/download/server</div>
        <div class="s-li">The spare PC connected to your lab network with a static IP of 192.168.50.10</div>
        <div class="s-li">A keyboard + monitor plugged in, or SSH access from your main PC</div>
        <div class="warn-box">⚠️ During the Ubuntu install, do NOT install the "Samba" snap — we will install it manually to get the AD DC version.</div>

        <div class="s-head">Step 1 — Set a Static IP on the Server</div>
        <div class="step-card">
            <div class="step-num">STEP 1</div>
            <div class="step-title">Assign a permanent IP address to your spare PC</div>
            <div class="step-body">Ubuntu uses Netplan for networking. Edit the config file:</div>
            <div class="cmd">sudo nano /etc/netplan/00-installer-config.yaml</div>
            <div class="step-body">Replace the contents with:</div>
            <div class="cmd">network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      addresses: [192.168.50.10/24]
      routes:
        - to: default
          via: 192.168.50.1
      nameservers:
        addresses: [127.0.0.1]</div>
            <div class="step-body">Save (Ctrl+O, Enter, Ctrl+X), then apply:</div>
            <div class="cmd">sudo netplan apply</div>
            <div class="note-box">The nameserver points to 127.0.0.1 (itself) because Samba 4 will become its own DNS server.</div>
        </div>

        <div class="s-head">Step 2 — Set the Hostname</div>
        <div class="step-card">
            <div class="step-num">STEP 2</div>
            <div class="step-title">Name the machine DC1 so it matches the domain</div>
            <div class="cmd">sudo hostnamectl set-hostname dc1.sentinel.local</div>
            <div class="step-body">Add it to /etc/hosts so the machine can resolve its own name:</div>
            <div class="cmd">sudo nano /etc/hosts</div>
            <div class="step-body">Add this line (replace any existing 127.0.1.1 line):</div>
            <div class="cmd">192.168.50.10   dc1.sentinel.local   dc1</div>
        </div>

        <div class="s-head">Step 3 — Install Samba 4</div>
        <div class="step-card">
            <div class="step-num">STEP 3</div>
            <div class="step-title">Install the Samba packages for Active Directory</div>
            <div class="cmd">sudo apt update && sudo apt install -y samba winbind krb5-config krb5-user</div>
            <div class="step-body">When prompted for the Kerberos realm, enter: <b style="color:#55ddf0;">SENTINEL.LOCAL</b></div>
            <div class="step-body">Stop the default Samba services — they conflict with AD DC mode:</div>
            <div class="cmd">sudo systemctl stop smbd nmbd winbind
sudo systemctl disable smbd nmbd winbind</div>
        </div>

        <div class="s-head">Step 4 — Provision the Domain</div>
        <div class="step-card">
            <div class="step-num">STEP 4</div>
            <div class="step-title">Create the SENTINEL.LOCAL domain — this is the core step</div>
            <div class="cmd">sudo samba-tool domain provision --use-rfc2307 --interactive</div>
            <div class="step-body">Answer the prompts:</div>
            <div class="cmd">Realm:           SENTINEL.LOCAL
Domain:          SENTINEL
Server role:     dc
DNS backend:     SAMBA_INTERNAL
Administrator password:   (choose something strong)</div>
            <div class="warn-box">⚠️ The Administrator password must be complex (uppercase, lowercase, number, symbol). Samba enforces this. Write it down somewhere safe.</div>
        </div>

        <div class="s-head">Step 5 — Start the Domain Controller</div>
        <div class="step-card">
            <div class="step-num">STEP 5</div>
            <div class="step-title">Enable and start the Samba AD DC service</div>
            <div class="cmd">sudo systemctl unmask samba-ad-dc
sudo systemctl enable --now samba-ad-dc</div>
            <div class="step-body">Verify it is running:</div>
            <div class="cmd">sudo systemctl status samba-ad-dc</div>
            <div class="step-body">Confirm the domain is responding:</div>
            <div class="cmd">sudo samba-tool domain info 127.0.0.1</div>
            <div class="note-box">You should see your domain name, DC name, and site listed. If you see an error, the most common cause is a DNS or hostname mismatch — re-check steps 1 and 2.</div>
        </div>

        <div class="s-head">Step 6 — Create User Accounts</div>
        <div class="step-card">
            <div class="step-num">STEP 6</div>
            <div class="step-title">Add the people who will log into the domain</div>
            <div class="cmd">sudo samba-tool user create alice "P@ssword123!"
sudo samba-tool user create bob   "P@ssword456!"
sudo samba-tool user create jeremiah "SecurePass789@"</div>
            <div class="step-body">List all users to confirm:</div>
            <div class="cmd">sudo samba-tool user list</div>
            <div class="step-body">To reset a password later:</div>
            <div class="cmd">sudo samba-tool user setpassword alice --newpassword="NewPass123!"</div>
            <div class="warn-box">⚠️ Use strong, unique passwords. In a shared lab environment, anyone with Domain Admin can read other users' hashes — treat this as a real security boundary.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — RASPBERRY PI FIREWALL
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown(
        """
        <div class="s-head">What the Pi Will Do</div>
        <div class="s-li">Act as a <b>NAT router</b> — all lab machines share your home internet connection through it</div>
        <div class="s-li">Run <b>iptables</b> to filter which traffic is allowed in and out of the lab</div>
        <div class="s-li">Run <b>Pi-hole</b> to block malware domains, trackers, and ads at the DNS level for every device in the lab — no client-side install needed</div>

        <div class="s-head">Hardware You Need</div>
        <div class="s-li">A Raspberry Pi (any model with two network interfaces — Pi 4 recommended)</div>
        <div class="s-li">A USB-to-Ethernet adapter (creates the second network port — eth1)</div>
        <div class="s-li">Raspberry Pi OS Lite (64-bit) installed — no desktop needed, lighter is better for a router</div>
        <div class="note-box">eth0 = the built-in Pi port → connect to your home router (WAN side)<br>
        eth1 = the USB adapter → connect to a switch that all lab machines plug into (LAN side)</div>

        <div class="s-head">Step 1 — Set a Static IP on the Pi's LAN Port</div>
        <div class="step-card">
            <div class="step-num">STEP 1</div>
            <div class="step-title">Give eth1 a permanent address — this becomes the lab's gateway</div>
            <div class="cmd">sudo nano /etc/dhcpcd.conf</div>
            <div class="step-body">Add at the bottom:</div>
            <div class="cmd">interface eth1
static ip_address=192.168.50.1/24</div>
            <div class="step-body">Reboot or restart the network service to apply.</div>
        </div>

        <div class="s-head">Step 2 — Enable IP Forwarding</div>
        <div class="step-card">
            <div class="step-num">STEP 2</div>
            <div class="step-title">Allow the Pi to pass packets between its two interfaces</div>
            <div class="cmd">echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p</div>
            <div class="step-body">This single line is what turns a Linux machine into a router. Without it, packets arriving on eth1 from the lab stay stuck there and can't reach the internet through eth0.</div>
        </div>

        <div class="s-head">Step 3 — Set Up NAT with iptables</div>
        <div class="step-card">
            <div class="step-num">STEP 3</div>
            <div class="step-title">Tell the Pi to rewrite source IPs on outgoing packets (masquerading)</div>
            <div class="cmd"># Let lab traffic out through the WAN port
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Allow return traffic for connections the lab initiated
sudo iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow lab → internet
sudo iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT

# Block unsolicited inbound connections from the internet to the lab
sudo iptables -A FORWARD -i eth0 -o eth1 -m conntrack --ctstate NEW -j DROP</div>
            <div class="note-box">The last rule is important for security — it drops any new connection attempts coming IN from the internet that weren't started by a lab machine. This is the firewall behavior.</div>
        </div>

        <div class="s-head">Step 4 — Save the Rules So They Survive Reboots</div>
        <div class="step-card">
            <div class="step-num">STEP 4</div>
            <div class="step-title">Make the firewall rules permanent</div>
            <div class="cmd">sudo apt install -y iptables-persistent
sudo netfilter-persistent save</div>
            <div class="step-body">Rules are now saved to /etc/iptables/rules.v4 and reload automatically at boot.</div>
        </div>

        <div class="s-head">Step 5 — Install Pi-hole (DNS Threat Blocking)</div>
        <div class="step-card">
            <div class="step-num">STEP 5</div>
            <div class="step-title">Add DNS-level protection for every device in the lab</div>
            <div class="cmd">curl -sSL https://install.pi-hole.net | bash</div>
            <div class="step-body">During setup, choose eth1 as the listening interface and set the static IP to 192.168.50.1. When asked for an upstream DNS provider, use 1.1.1.1 (Cloudflare) or 8.8.8.8 (Google).</div>
            <div class="step-body">After install, access the Pi-hole admin panel from any lab browser:</div>
            <div class="cmd">http://192.168.50.1/admin</div>
            <div class="step-body">
                Pi-hole maintains millions of known malware, phishing, and tracker domains in blocklists.
                Any device that uses it as its DNS server (set DNS to 192.168.50.1) is automatically protected
                without installing anything on that device.
            </div>
            <div class="warn-box">⚠️ Important: Domain-joined Windows clients must use the DC (192.168.50.10) as their DNS, not Pi-hole, or domain lookups will break. Configure Pi-hole to forward .local queries to the DC by adding a custom DNS entry: sentinel.local → 192.168.50.10.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — JOIN & USE
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown(
        """
        <div class="s-head">Domain Join a Windows PC</div>
        <div class="step-card">
            <div class="step-num">STEP 1</div>
            <div class="step-title">Point the Windows PC's DNS at the Domain Controller</div>
            <div class="step-body">Open Network Settings → Change adapter options → Right-click your network adapter → Properties → Internet Protocol Version 4 → Use the following DNS server:</div>
            <div class="cmd">Preferred DNS:  192.168.50.10   (the Samba DC)
Alternate DNS:  (leave blank)</div>
            <div class="note-box">This is the most important step. If Windows cannot resolve SENTINEL.LOCAL via DNS, domain join will fail with a confusing error. Test it first: open Command Prompt and run <b>nslookup sentinel.local 192.168.50.10</b> — you should see the DC's IP returned.</div>
        </div>

        <div class="step-card">
            <div class="step-num">STEP 2</div>
            <div class="step-title">Join the domain through System Properties</div>
            <div class="step-body">Right-click Start → System → Rename this PC (advanced) → Change → select Domain and enter:</div>
            <div class="cmd">SENTINEL.LOCAL</div>
            <div class="step-body">When prompted for credentials, enter:</div>
            <div class="cmd">Username:  Administrator
Password:  (the password you set during samba-tool domain provision)</div>
            <div class="step-body">Click OK. Windows will say "Welcome to the SENTINEL.LOCAL domain." Restart the PC.</div>
        </div>

        <div class="step-card">
            <div class="step-num">STEP 3</div>
            <div class="step-title">Log in with a domain account</div>
            <div class="step-body">At the Windows login screen, click "Other user" and type:</div>
            <div class="cmd">Username:  SENTINEL\\alice
Password:  P@ssword123!</div>
            <div class="step-body">Windows contacts the DC, Kerberos issues a TGT, and Alice is logged in — her profile is created locally on first login.</div>
        </div>

        <div class="s-head">Manage the Domain (from Windows with RSAT)</div>
        <div class="step-card">
            <div class="step-num">RSAT</div>
            <div class="step-title">Install Remote Server Administration Tools — free Windows feature</div>
            <div class="step-body">On a domain-joined Windows 10/11 PC, open Settings → Optional Features → Add a feature → search for and install:</div>
            <div class="cmd">RSAT: Active Directory Domain Services and Lightweight Directory Tools</div>
            <div class="step-body">After install, open Start → Windows Administrative Tools → Active Directory Users and Computers. You now have a full graphical interface to manage users, groups, OUs, and Group Policy — the same tools an enterprise sysadmin uses every day.</div>
        </div>

        <div class="s-head">Group Policy — Enforce Rules on Every Machine</div>
        <div class="step-card">
            <div class="step-num">GPO</div>
            <div class="step-title">Push settings to every domain-joined PC from one place</div>
            <div class="step-body">In RSAT, open Group Policy Management. Right-click your domain and create a GPO. Some useful policies to explore:</div>
            <div class="cmd">Computer Configuration → Windows Settings → Security Settings:
  - Account Policies → Password Policy → Minimum length: 12
  - Account Lockout Policy → Threshold: 5 attempts

User Configuration → Administrative Templates:
  - Control Panel → Prohibit access to Control Panel (lock down users)
  - System → Removable Disks → Deny write access (block USB data theft)
  - Desktop → Desktop Wallpaper → Set a custom wallpaper for all users</div>
            <div class="step-body">After editing a GPO, domain-joined machines pick up the change at next login or when you run:</div>
            <div class="cmd">gpupdate /force</div>
        </div>

        <div class="s-head">Cybersecurity Skills This Lab Teaches You</div>
        <div class="s-li">How authentication tickets (Kerberos TGT and service tickets) work in practice — a core concept in attacks like Pass-the-Ticket and Golden Ticket.</div>
        <div class="s-li">How Group Policy propagates — and why misconfigured GPOs are one of the most common ways attackers escalate privileges in a real engagement.</div>
        <div class="s-li">How to enumerate AD with tools like BloodHound and ldapsearch — you need a real domain to run them against.</div>
        <div class="s-li">How iptables firewall rules actually behave, what NAT masquerading does at the packet level, and how Pi-hole intercepts DNS to block threats.</div>
        <div class="s-li">The difference between local accounts and domain accounts — and why attackers always target the domain instead of individual machines.</div>
        <div class="note-box">
            <b>Next level:</b> Once your lab is running, try installing BloodHound CE (free) on a domain-joined machine, run the SharpHound data collector, and visualize the attack paths through your own domain. It will show you exactly what a red teamer would exploit. Then lock those paths down with GPO and re-run to confirm the fix.
        </div>
        """,
        unsafe_allow_html=True,
    )
