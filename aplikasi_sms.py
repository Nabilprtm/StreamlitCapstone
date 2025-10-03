import pickle
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from sklearn.feature_extraction.text import TfidfVectorizer
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode
import os, json, hashlib

# ============== [LOGIN PAGE – tempel di atas kode aplikasimu] ==============

USERS_FILE = "Model/users.json"

# Default akun bawaan (akan di-seed ke users.json jika file kosong)
USERS = {"danny": "12345", "admin": "admin123"}

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def _load_users() -> dict:
    """Load users dari JSON, seed dengan USERS default kalau file belum ada."""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    data = {}
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
        except Exception:
            data = {}
    users = data.get("users", {})

    # Seed default
    for uname, pw in USERS.items():
        users.setdefault(uname, _hash(pw))

    # Tulis balik supaya file selalu ada
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, indent=2, ensure_ascii=False)
    return users

def _save_users(users: dict) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, indent=2, ensure_ascii=False)

st.set_page_config(page_title="Deteksi SMS Spam", page_icon="📱", layout="wide")

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

def login_ui():
    # Styling
    st.markdown("""
    <style>
      .nav-item {
        display:flex; align-items:center; gap:10px;
        padding:10px 12px; border-radius:10px; margin:6px 0; font-weight:600;
      }
      .nav-item.active { background:#7C3AED; color:#fff; }
      .title-blue { color:#1E90FF; text-align:center; margin-bottom:12px; }
    </style>
    """, unsafe_allow_html=True)

    # State tampilan (Login/Create/Forgot/Reset)
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "Login"

    # 3 kolom utama
    col_nav, col_center, col_img = st.columns([1.2, 1.6, 1.2], gap="large")

   # --- KIRI: Judul + Navigation (styled kotak, bukan radio)
    with col_nav:
        with st.container(border=True):
            st.markdown("<h3 class='title-blue'>📱 Aplikasi Deteksi SMS Spam</h3>", unsafe_allow_html=True)

            # tombol navigasi
            if st.button("📥 Login", use_container_width=True):
                st.session_state.auth_view = "Login"
            if st.button("👤 Create Account", use_container_width=True):
                st.session_state.auth_view = "Create Account"
            if st.button("❓ Forgot Password?", use_container_width=True):
                st.session_state.auth_view = "Forgot Password?"
            if st.button("🔄 Reset Password", use_container_width=True):
                st.session_state.auth_view = "Reset Password"


    # --- TENGAH: Konten sesuai pilihan
    with col_center:
        with st.container(border=True):
            users = _load_users()  # baca users.json

            if st.session_state.auth_view == "Login":
                st.subheader("Login")
                with st.form("login_form"):
                    u = st.text_input("Username", placeholder="Your unique username")
                    show_pw = st.checkbox("Show password", value=False)
                    p = st.text_input("Password", type=("default" if show_pw else "password"), placeholder="Your password")
                    submitted = st.form_submit_button("Login")

                st.caption("Silahkan Masukkan Username & Password Dengan Benar")

                if submitted:
                    if u.strip() == "" or p.strip() == "":
                        st.warning("Isi username dan password.")
                    elif u not in users:
                        st.error("Username tidak terdaftar.")
                    elif users[u] != _hash(p):
                        st.error("Password salah.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user = u
                        st.success("Login berhasil. Memuat aplikasi…")
                        st.rerun()

            elif st.session_state.auth_view == "Create Account":
                st.subheader("Create Account")
                with st.form("register_form"):
                    ru = st.text_input("Username baru", placeholder="mis. nabil_01")
                    rp1 = st.text_input("Password", type="password", placeholder="Minimal 5 karakter")
                    rp2 = st.text_input("Ulangi password", type="password", placeholder="Ketik ulang password")
                    agree = st.checkbox("Saya setuju membuat akun baru")
                    r_sub = st.form_submit_button("Daftar")

                if r_sub:
                    ru_clean = ru.strip()
                    if not agree:
                        st.warning("Centang persetujuan terlebih dahulu.")
                    elif ru_clean == "" or rp1.strip() == "" or rp2.strip() == "":
                        st.warning("Semua kolom wajib diisi.")
                    elif len(ru_clean) < 4:
                        st.warning("Username minimal 4 karakter.")
                    elif len(rp1) < 5:
                        st.warning("Password minimal 5 karakter.")
                    elif rp1 != rp2:
                        st.error("Password dan konfirmasi tidak sama.")
                    elif ru_clean in users:
                        st.error("Username sudah digunakan.")
                    else:
                        users[ru_clean] = _hash(rp1)
                        _save_users(users)
                        st.success("Akun berhasil dibuat. Anda akan otomatis masuk…")
                        st.session_state.logged_in = True
                        st.session_state.user = ru_clean
                        st.rerun()

            elif st.session_state.auth_view == "Forgot Password?":
                st.subheader("Forgot Password?")
                st.info("Hubungi admin untuk reset password, atau gunakan tab **Reset Password** bila Anda tahu username-nya.")
                st.text_input("Username terdaftar")

            else:  # Reset Password
                st.subheader("Reset Password")
                with st.form("reset_form"):
                    ru = st.text_input("Username")
                    old = st.text_input("Password lama", type="password")
                    new1 = st.text_input("Password baru", type="password")
                    new2 = st.text_input("Ulangi password baru", type="password")
                    do = st.form_submit_button("Reset")

                if do:
                    if ru not in users:
                        st.error("Username tidak ditemukan.")
                    elif users[ru] != _hash(old):
                        st.error("Password lama salah.")
                    elif len(new1) < 5:
                        st.warning("Password baru minimal 5 karakter.")
                    elif new1 != new2:
                        st.error("Konfirmasi password baru tidak sama.")
                    else:
                        users[ru] = _hash(new1)
                        _save_users(users)
                        st.success("Password berhasil direset. Silakan login kembali.")
                        st.session_state.auth_view = "Login"
                        st.rerun()

    # --- KANAN: Ilustrasi
    with col_img:
        with st.container(border=True):
            st.image("Assets/smslogo.png", use_container_width=True)

# Gate: tampilkan login dulu
if not st.session_state.logged_in:
    login_ui()
    st.stop()

# (Opsional) panel mini user + Logout di sidebar
with st.sidebar:
    st.markdown(
        f"""
        <div style="background:#EAF4FF22;border:1px solid #BBD8FF55;padding:12px;border-radius:12px;margin-bottom:8px;">
            <strong>👤 Login sebagai:</strong><br>{st.session_state.user}
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
# ==================== [END LOGIN PAGE] ====================


# Load saved model and vectorizer
@st.cache_resource
def load_model_and_vectorizer():
    model = pickle.load(open('Model/model_fraud.sav', 'rb'))
    vocab = pickle.load(open("Model/new_selected_feature_tf-idf.sav", "rb"))
    vectorizer = TfidfVectorizer(decode_error="replace", vocabulary=vocab)
    # Fit the vectorizer with dummy data to avoid NotFittedError
    vectorizer.fit(["dummy data"])
    return model, vectorizer

model_fraud, loaded_vec = load_model_and_vectorizer()

# Sidebar dengan option menu
with st.sidebar:
    page = option_menu(
        "Menu Navigasi",
        ["Informasi SMS Spam", "Panduan Aplikasi", "Aplikasi Deteksi SMS", "Tentang Saya"],
        icons=["info-circle", "book", "search", "table", "person"],
        menu_icon="cast",
        default_index=0,
        styles={
            "nav-link-selected": {"background-color": "#68ADFF", "color": "white"},
        },
    )
    st.markdown(
        """
        <div style="margin-top: 90px;">
            <strong>Versi Aplikasi:</strong> 1.0.0
        <br>
        <small>&copy; 2025 by @KelompokCP Danny Nabil</small>
        </div>
        """,
        unsafe_allow_html=True
    )

# Halaman Tentang SMS Spam
if page == "Informasi SMS Spam":
    #ARTIKEL KE-1
    st.title('Apasih SMS Spam itu?')
    st.markdown(
        """
        <div style="text-align: justify;">
            <p>Kalian pernah penasaran sebenarnya SMS spam itu apa? Apakah berbahaya? Weets, tenang dulu ya guys karena di sini saya akan menjelaskan lebih lanjut tentang isu ini, let's gooo.</p>
            <p>Secara umum SMS spam adalah pesan teks yang tidak diinginkan yang dikirim secara besar-besaran kepada banyak penerima.</p>
            <p>Pesan ini sering kali mengandung tawaran promosi, penipuan, atau informasi yang tidak berkaitan. SMS spam dapat mengacaukan dan menguras sumber daya pada perangkat penerima.</p>
            <p>Oleh karena itu, dengan teknologi deteksi SMS spam, kita bisa menyaring dan mengategorikan pesan-pesan ini untuk mengurangi efek buruknya.</p> 
        </div>
        <br><br><br>
        """,
        unsafe_allow_html=True
    )
    st.image("Assets/spamsms.png", caption="Gambar SMS spam", use_container_width=True)
    st.write("<br><br>", unsafe_allow_html=True)

    #ARTIKEL KE-2
    st.title('Jenis Dan Tujuan SMS Spam')
    st.image("Assets/notification.gif",caption="Animasi notifikasi masuk", use_container_width=True)
    st.write("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align: justify;">
            Berdasarkan penjelasan tentang arti spam yang telah disampaikan, berikut adalah beberapa tujuan spam yang perlu kita ketahui:
        <br>
        <h3>1. Skema Penipuan</h3>
        <p>Beberapa SMS Spam dibuat untuk menyesatkan penerima. Contohnya, sebuah pesan bisa menginformasikan bahwa penerima telah berhasil memenangkan hadiah atau lotere, meminta mereka membayar biaya untuk mengambil hadiah itu. Hal ini dapat mengakibatkan kerugian finansial bagi penerima.</p>

        <h3>2. Phishing</h3>
        <p>SMS phishing berusaha mendapatkan informasi sensitif, seperti nomor kartu kredit atau kata sandi. Pesan ini mungkin mengarahkan penerima ke situs web palsu yang terlihat mirip dengan situs resmi, di mana mereka diminta untuk memasukkan informasi pribadi.</p>

        <h3>3. Jenis Iklan Yang Menggangu</h3>
        <p>Banyak bisnis menggunakan SMS spam untuk mengirimkan iklan tanpa izin penerima. Ini sering kali dianggap sebagai gangguan dan dapat merusak reputasi pengirim.</p>

        <h3>4. Penawaran Jasa Keuangan</h3>
        <p>Beberapa pesan menawarkan layanan keuangan, seperti pinjaman atau investasi. Banyak dari layanan ini mungkin tidak sah atau memiliki syarat yang merugikan.</p>
        </div>
        
        """,
        unsafe_allow_html=True
    )
    st.write("<br><br>", unsafe_allow_html=True)

    #ARTIKEL KE-3
    st.title('Dampak Buruk SMS Spam')
    st.image("Assets/thinking.gif",caption="Animasi memikirkan jenis pesan",use_container_width=True)
    st.markdown(
        """
        <div style="text-align: justify;">
            <p>Seperti yang kita ketahui bahwa pesan SMS yang kita terima memiliki berbagai jenis pesan-pesan yang masuk.</p>
            <p>Namun, tahukah kalian bahwa di antara berbagai pesan yang masuk, tidak sedikit yang tergolong sebagai pesan spam.</p>
            <p>Meskipun sekilas pesan spam tampak seperti teks biasa, pada kenyataannya pesan tersebut dapat menimbulkan dampak yang merugikan jika tidak disikapi dengan kewaspadaan.</p>
        <br><br>
        Selain itu, banyaknya cara penipuan yang hanya dikirim lewat SMS, jadi kami hanya ingin membagikan beberapa dampak negatif SMS Spam bagi individu, antara lain sebagai berikut:
        <br>
        <ol>
            <li>Spam kerap dimanfaatkan untuk melakukan phishing, yaitu upaya penipuan yang bertujuan memperoleh informasi pribadi seperti nomor kartu kredit, kata sandi, dan data sensitif lainnya.</li>
            <li>Beberapa pesan spam mengandung tautan atau lampiran berbahaya yang dapat menyebarkan malware dan menginfeksi perangkat penerima untuk mencuri data penting.</li>
            <li>Korban yang tergiur oleh spam yang menawarkan hadiah, lotere, atau investasi palsu berisiko mengalami kerugian finansial yang cukup besar.</li>
            <li>Penggunaan identitas palsu dalam pesan spam dapat menimbulkan kesalahpahaman dan merusak hubungan sosial antara pengirim dan penerima.</li>
            <li>Spam juga dapat menghabiskan sumber daya perangkat secara tidak efisien, seperti ruang penyimpanan, baterai, dan kinerja sistem secara keseluruhan.</li>
        </ol>

        </div>
        
        """,
        unsafe_allow_html=True
    )
    
    
# Halaman Panduan Aplikasi
elif page == "Panduan Aplikasi":
    st.title('Langkah-Langkah Penggunaan Aplikasi')
    st.write("<br>", unsafe_allow_html=True)
    #LANGKAH 1
    st.markdown(
        """
        <div style="text-align: justify;">
            Agar kalian tidak bingung saat menggunakan aplikasi deteksi ini, kami jelasin caranya, ya!😊.Sebenarnya caranya cukup sederhana, tapi tidak ada salahnya kami bantu jelaskan supaya kalian makin paham dan sekalian bisa baca-baca juga. Nah, langsung saja berikut ini langkah-langkah penggunaannya:
        <br><br>
        <ol start="1">
        <li>Untuk memulai cara penggunaan aplikasi deteksi spam,langkah pertama kita pilih menu pada bagian “Aplikasi Deteksi SMS” pada halaman sidebar menu navigasi dan kita dapat melihat sebuah tampilan dari sistem deteksi SMS spam seperti gambar dibawah ini:</p>
        </li>
        <br>
        """,
        unsafe_allow_html=True
    )
    st.image("Assets/LANGKAH1.PNG",caption="Gambar panduan pertama",use_container_width=True)

    #LANGKAH 2
    st.markdown(
        """
        <br><br>
        <div style="text-align: justify;">
        <ol start="2">
        <li>Kemudian sekarang kita akan memasukkan sebuah teks pesan SMS kita yang ada di HP kita masing-masing dengan cara copy and paste ke area input-text area halaman deteksi.Setelah kalian sudah menginput teks yang kalian pilih, kemudian tekan tombol “Deteksi” untuk melihat hasil output yang akan ditampilkan seperti gambar dibawah ini:</p>
        </li>
        <br>
        """,
        unsafe_allow_html=True
    )
    st.image("Assets/LANGKAH2.PNG",caption="Gambar panduan kedua",use_container_width=True)

    #LANGKAH 3
    st.markdown(
        """
        <br><br>
        <div style="text-align: justify;">
        <ol start="3">
        <li>Yeyy, sudah deh. Hasil deteksi pesan yang tadi sudah kita input menunjukkan bahwa pesan tersebut merupakan jenis SMS normal yang artinya aman untuk direspon/ditanggapi dan tidak ada terindikasi bahwa pesan tersebut spam.</p>
        </li>
        <br>
        """,
        
        unsafe_allow_html=True
    )
    st.image("Assets/LANGKAH3.PNG",caption="Gambar hasil deteksi",use_container_width=True)

# Halaman Aplikasi Deteksi
elif page == "Aplikasi Deteksi SMS":
    st.title('Sistem Deteksi SMS Spam')

    st.markdown(
        """
        <style>
        textarea {
            font-size: 20px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    sms_text = st.text_area("Masukkan Teks SMS Dibawah Ini")
    if st.button('Cek Deteksi'):
        clean_teks = sms_text.strip()

        if clean_teks == "":
            spam_detection = "Mohon Masukkan Pesan Teks SMS"
            st.markdown(
                f"""
                <div style="border: 2px; border-radius: 15px; padding: 2px; display: flex; align-items: center; background-color: #1F211D;">
                    <div style="color: #F1C40F; font-size: 25px; margin-left: 10px;"><strong>{spam_detection}</strong></div>
                    <iframe src="https://lottie.host/embed/c006c08e-3a86-47e6-aaae-3e11674c204b/cQiwVs5lkD.json" style="width: 100px; height: 100px;"></iframe>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            transformed_text = loaded_vec.transform([clean_teks])
            predict_spam = model_fraud.predict(transformed_text.toarray())

            if predict_spam == 0:
                spam_detection = "SMS NORMAL"
                st.markdown(
                    f"""
                    <div style="border: 2px solid #177233; border-radius: 15px; padding: 10px; display: flex; align-items: center; background-color: #D6F9B7;">
                        <div style="flex: 1;">
                            <div style="color: #177233; font-size: 25px; margin-left: 10px;">
                                <strong>{spam_detection}</strong>
                            </div>
                            <div style="background-color: white; border-radius: 5px; padding: 5px; margin-top: 10px;">
                                <ul style="color: #177233; font-size: 18px; list-style-type: none; padding: 0; margin: 0;">
                                    <li>Pesan SMS ini bukan termasuk pesan spam promo/penipuan</li>
                                    <li>melainkan pesan normal pada umumnya dan aman untuk ditanggapi</li>
                                </ul>
                            </div>
                        </div>
                        <iframe src="https://lottie.host/embed/94ef5ba2-ff8e-4b1a-868b-6a6a926cfca0/D3oNNvId2Y.json" style="width: 120px; height: 120px;"></iframe>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            elif predict_spam == 1:
                spam_detection = "SMS PENIPUAN"
                st.markdown(
                    f"""
                    <div style="border: 2px solid #D90000; border-radius: 15px; padding: 10px; display: flex; align-items: center; background-color: #FF9590;">
                        <div style="flex: 1;">
                            <div style="color: #D90000; font-size: 25px; margin-left: 10px;">
                                <strong>{spam_detection}</strong>
                            </div>
                            <div style="background-color: white; border-radius: 5px; padding: 5px; margin-top: 10px;">
                                <ul style="color: #F00B00; font-size: 18px; list-style-type: none; padding: 0; margin: 0;">
                                    <li>Pesan SMS ini terindikasi pesan spam penipuan</li>
                                    <li>dikarenakan terdapat informasi yang mencurigakan</li>
                                </ul>
                            </div>
                        </div>
                        <iframe src="https://lottie.host/embed/66044930-6b4e-4546-9765-4fcf4a98ca37/U6WsPr1BHE.json" style="width: 120px; height: 120px;"></iframe>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            elif predict_spam == 2:
                spam_detection = "SMS PROMO"
                st.markdown(
                    f"""
                    <div style="border: 2px solid #3773D6; border-radius: 15px; padding: 10px; display: flex; align-items: center; background-color: #C3E6FF;">
                        <div style="flex: 1;">
                            <div style="color: #3773D6; font-size: 25px; margin-left: 10px;">
                                <strong>{spam_detection}</strong>
                            </div>
                            <div style="background-color: white; border-radius: 5px; padding: 5px; margin-top: 10px;">
                                <ul style="color: #3773D6; font-size: 18px; list-style-type: none; padding: 0; margin: 0;">
                                    <li>Pesan SMS ini adalah spam promo yang menawarkan penawaran khusus</li>
                                    <li>untuk membeli/menggunakan promo yang diberikan</li>
                                </ul>
                            </div>
                        </div>
                        <iframe src="https://lottie.host/embed/62ea7f76-6873-4024-9081-cd6cdf8a7246/amgyWxn0IT.json" style="width: 120px; height: 120px;"></iframe>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# Halaman Tentang Kami
elif page == "Tentang Saya":    
    st.markdown("""
    <div style="text-align: center;">
        <h2 style="color: #68ADFF;">👨‍💻 Tentang Kami</h2>
        <p style="font-size: 17px;">Kami adalah tiga mahasiswa penuh semangat dari <strong>UNP KEDIRI</strong> yang memiliki satu misi: <em>membuat teknologi bermanfaat, mudah diakses, dan berdampak nyata.</em></p>
        <p style="font-size: 17px;">Dikarenakan ada tugas mata kuliah Capstone Project dan kebetulan sekarang lagi marak penipuan lewat SMS, kami pun berinisiatif membuat aplikasi untuk mendeteksi pesan-pesan yang berpotensi penipuan. Semoga bisa membantu banyak orang lebih waspada!</p>    
    </div>

    <div style="background-color: #F0F8FF; padding: 20px; border-radius: 15px;">
    <h3 style="color: #1F618D;">🚀 Tim Pengembang:</h3>
    <ul style="font-size: 16px; list-style-type: square; color: #1A1A1A;">
        <li><strong>🧑‍💻 Muhammad Nabil Pratama</strong> – Master di bagian pengumpulan pesan SMS untuk membangun dataset guyss.</li>
        <li><strong>🎨 Danny Putra Ardianto</strong> – Frontend dan pembangunan bagian aplikasi SMS nya ya guyss.</li>
    </ul>
    </div>

    <br>

    <div style="background-color: #FFF7E8; padding: 20px; border-radius: 15px;">
    <h3 style="color: #E67E22;">🎯 Misi Aplikasi</h3>
    <p style="font-size: 16px; color: #1A1A1A;">
        Aplikasi ini kami bangun sebagai bentuk solusi atas maraknya SMS spam, penipuan, dan promo tidak relevan. 
        Dengan teknologi <strong>Machine Learning</strong> menggunakan algoritma <strong>Support Vector Machine (SVM)</strong> 
        dan antarmuka <strong>Streamlit</strong>, kami ingin menghadirkan sistem deteksi SMS yang cerdas namun tetap ramah pengguna.
    </p>
    </div>


    <br>

    <div style="background-color: #E8F8F5; padding: 20px; border-radius: 15px;">
        <h3 style="color: #148F77;">📬 Hubungi Kami</h3>
        <ul style="font-size: 16px; color: #1A1A1A;">
            <li>Email: kelompok6.smartapps@gmail.com</li>
            <li>GitHub: <a href="https://github.com/kelompokCP-deteksisms" target="_blank">github.com/kelompokCP-deteksisms</a></li>
        </ul>
    </div>

    <br>

    <div style="text-align: center;">
        <p style="font-size: 15px;"><em>“Karena pesan spam itu bukan cuma gangguan... tapi bisa jadi bencana 👀.”</em></p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("Assets/PROFILE.jpg", caption="Profil Kami", use_container_width=True)



# Footer
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: calc(100% - 20rem);
        margin-left: -5rem;
        background-color: #7DB8FF;
        color: black;
        text-align: center;
        padding: 5px 0;
        height: 50px;
        font-size: 14px;
        border-top: 2px solid #e0e0e0;
        z-index: 1000;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    @media (max-width: 2500px) {
        .footer {
            width: 100%;
            margin-left: 0;
        }
    }
    .minimized-sidebar .footer {
        width: 100%;
        margin-left: 0;
    }
    </style>
    <div class="footer"></div>
    """,
    unsafe_allow_html=True
)
