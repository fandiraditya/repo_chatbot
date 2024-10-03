import streamlit as st
import pandas as pd
import re
from Ask_me_ import load_data_pht, build_context_and_response, get_answer, build_context_and_response_mitigasi

# Syntax guide for user interaction
with st.expander("Available Syntax (How to ask questions)"):
    st.write("""
    You can ask the chatbot the following types of questions:
    
    1. **Total PHT in a region**:
       - "Total PHT wilayah [Wilayah]"
       - Example: "Berapa total PHT wilayah Jakarta?"
    
    2. **Derating conductors**:
       - "Derating penghantar"
       - Example: "Penghantar yang derating mana saja?"
    
    3. **List of PHT regions**:
       - "Wilayah PHT"
       - Example: "Wilayah PHT mana saja?"
    
    4. **List of all PHT conductors**:
       - "Daftar penghantar PHT"
       - Example: "Daftar penghantar PHT"
    
    5. **Total number of conductors**:
       - "Berapa jumlah penghantar?"
       - Example: "Berapa jumlah penghantar?"

    6. **Conductor with the highest current**:
       - "Penghantar dengan arus terbesar"
       - Example: "Penghantar dengan arus terbesar"

    7. **Details of a specific conductor**:
       - "Detail penghantar dari Gitet [Gitet1] ke Gitet [Gitet2]"
       - Example: "Detail penghantar dari Gitet A ke Gitet B"
    """)

# Tampilan utama dengan Streamlit
st.title('Chatbot Informasi Data PHT dengan Jawaban Deskriptif')

# Memuat data dari file excel
data_pht, data_mitigasi = load_data_pht()  # Split the tuple into two separate dataframes

st.write("Berikut adalah beberapa data yang tersedia:")
st.write(data_pht.head())  # Menampilkan beberapa baris data
st.write("Berikut adalah beberapa data mitigasi yang tersedia:")
st.write(data_mitigasi.head())  # Menampilkan beberapa baris data mitigasi

# Input dari pengguna
keyword = st.text_input("Masukkan kata kunci (misal: nama Lokasi Gitet/Gistet):")

# Checkbox for highlighting option
highlight_option = st.checkbox("Highlight keyword?", value=True)

# Helper function to remove HTML highlighting tags
def strip_html_tags(text, keyword):
    return re.sub(r'<.*?>', '', text).replace(f'<span style="background-color: yellow">{keyword.upper()}</span>', keyword.upper())

# Jika input sudah diisi
if st.button("Cari Informasi"):
    if keyword:
        # Bangun konteks berdasarkan kata kunci untuk PHT
        st.write('Mencari informasi PHT...')
        context_pht, response_pht = build_context_and_response(data_pht, keyword)

        # Bangun konteks berdasarkan kata kunci untuk mitigasi
        st.write('Mencari informasi mitigasi...')
        context_mitigasi, response_mitigasi = build_context_and_response_mitigasi(data_mitigasi, keyword)

        # Use tabs to display the results separately
        tab1, tab2 = st.tabs(["PHT Information", "Mitigasi Information"])

        # Tab 1: PHT Information
        with tab1:
            st.write("Informasi PHT yang ditemukan:")
            if highlight_option:
                # Render the highlighted response
                st.markdown(response_pht, unsafe_allow_html=True)
            else:
                # Strip HTML and render plain text without HTML tags
                stripped_response_pht = strip_html_tags(response_pht, keyword)
                st.write(stripped_response_pht)

        # Tab 2: Mitigasi Information
        with tab2:
            st.write("Informasi mitigasi yang ditemukan:")
            if highlight_option:
                # Render the highlighted response
                st.markdown(response_mitigasi, unsafe_allow_html=True)
            else:
                # Strip HTML and render plain text without HTML tags
                stripped_response_mitigasi = strip_html_tags(response_mitigasi, keyword)
                st.write(stripped_response_mitigasi)

    else:
        st.write("Harap masukkan kata kunci untuk pencarian.")

# Chat interaktif - Input pertanyaan pengguna
user_question = st.text_input("Ajukan pertanyaan tentang data ini:")

# Helper function to handle user questions about the data
def handle_user_question(question, data_pht, data_mitigasi):
    question = question.lower()

    if "total pht" in question:
        # Respond with total PHT for a given wilayah
        wilayah = st.text_input("Masukkan wilayah UPT yang ingin dicari:")
        if wilayah:
            total_pht = data_pht[data_pht['Wilayah'].str.contains(wilayah, case=False)]['Panjang Penghantar'].sum()
            return f"Total PHT di wilayah {wilayah.capitalize()} adalah {total_pht} km."
    
    elif "derating" in question:
        # List penghantar that have derating
        derating_data = data_pht[~data_pht['Keterangan Penyebab Derating'].isna()]
        if derating_data.empty:
            return "Tidak ada penghantar yang mengalami derating."
        else:
            penghantar_list = derating_data[['Dari Gitet/Gistet', 'Ke Gitet/Gistet', 'Keterangan Penyebab Derating']]
            return penghantar_list.to_string(index=False)

    elif "wilayah pht" in question:
        # List unique regions for PHT
        wilayah_list = data_pht['Wilayah'].unique()
        return f"Wilayah yang terdaftar untuk PHT: {', '.join(wilayah_list)}"
    
    elif "daftar penghantar pht" in question:
        # List all PHT conductors
        penghantar_list = data_pht[['Dari Gitet/Gistet', 'Ke Gitet/Gistet', 'Panjang Penghantar']]
        return penghantar_list.to_string(index=False)
    
    elif "jumlah penghantar" in question:
        # Count total conductors
        jumlah_penghantar = len(data_pht)
        return f"Jumlah penghantar PHT: {jumlah_penghantar}"
    
    elif "arus terbesar" in question:
        # Find conductor with the highest nominal current
        penghantar_terbesar = data_pht.loc[data_pht['Nominal Arus (A)'].idxmax()]
        return f"Penghantar dengan arus terbesar adalah dari {penghantar_terbesar['Dari Gitet/Gistet']} ke {penghantar_terbesar['Ke Gitet/Gistet']} dengan arus {penghantar_terbesar['Nominal Arus (A)']} A."
    
    elif "detail penghantar" in question:
        # Fetch details of a specific conductor
        gitet1 = st.text_input("Masukkan nama Gitet asal:")
        gitet2 = st.text_input("Masukkan nama Gitet tujuan:")
        if gitet1 and gitet2:
            detail = data_pht[(data_pht['Dari Gitet/Gistet'].str.contains(gitet1, case=False)) & 
                              (data_pht['Ke Gitet/Gistet'].str.contains(gitet2, case=False))]
            if detail.empty:
                return f"Tidak ada detail untuk penghantar dari Gitet {gitet1.capitalize()} ke Gitet {gitet2.capitalize()}."
            else:
                return detail.to_string(index=False)

    else:
        # Default response if no condition is met
        return "Pertanyaan tidak dikenali. Harap coba dengan kata kunci yang berbeda."

# Handle the user's question
if user_question:
    response = handle_user_question(user_question, data_pht, data_mitigasi)
    st.write(response)
