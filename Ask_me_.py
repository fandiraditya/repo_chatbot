import pandas as pd
from transformers import pipeline
import re  # Import the re module

# Fungsi untuk memuat data dari file excel yang sudah tersedia
def load_data_pht():
    df_pht = pd.read_excel('DataPHT.xlsx')
    df_mitigasi = pd.read_excel('500kV Transmission Line Contingencies_Updated.xlsx', sheet_name='Contingency')
    return df_pht, df_mitigasi

# Inisialisasi pipeline dari Hugging Face Transformers untuk pertanyaan-jawaban (Q&A)
qa_model = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

# Fungsi untuk mencari data berdasarkan kata kunci, tidak peka terhadap huruf besar/kecil
def search_data(df, keyword):
    # Convert semua kolom dan baris ke huruf kecil untuk pencarian case-insensitive
    df_lower = df.applymap(lambda s: s.lower() if isinstance(s, str) else s)
    keyword_lower = keyword.lower()  # Konversi keyword menjadi huruf kecil
    
    # Cari data yang mengandung kata kunci di salah satu kolom
    result = df_lower[df_lower.apply(lambda row: row.astype(str).str.contains(keyword_lower).any(), axis=1)]
    
    if result.empty:
        return None
    else:
        return result

# Fungsi untuk membangun konteks dari data dan menyusun respons deskriptif
def build_context_and_response(df, keyword):
    # Cari data berdasarkan kata kunci (case-insensitive)
    result = search_data(df, keyword)
    
    if result is None:
        return None, "Data tidak ditemukan untuk kata kunci yang diminta."
    else:
        # Convert the keyword to highlighted text using a span tag with background color
        keyword_highlighted = f'<span style="background-color: yellow">{keyword.upper()}</span>'
        
        # Menyusun kalimat deskriptif untuk setiap baris yang ditemukan
        responses = []
        for index, row in result.iterrows():
            dari_gitet = row['Dari Gitet/Gistet'].capitalize()
            ke_gitet = row['Ke Gitet/Gistet'].capitalize()
            panjang = row['Panjang Penghantar'] if not pd.isnull(row['Panjang Penghantar']) else 'tidak tersedia'
            nominal = row['Nominal Arus (A)'] if not pd.isnull(row['Nominal Arus (A)']) else 'tidak tersedia'
            kemampuan_max = row['Kemampuan Penghantar (A)'] if not pd.isnull(row['Kemampuan Penghantar (A)']) else 'tidak tersedia'
            wilayah = row['Wilayah'].upper() if not pd.isnull(row['Wilayah']) else 'tidak tersedia'
            derating = row['Keterangan Penyebab Derating'] if not pd.isnull(row['Keterangan Penyebab Derating']) else 'tidak derating'
            persen_derating = row['Deklarasi Kemampuan (%)'] if not pd.isnull(row['Deklarasi Kemampuan (%)']) else 'tidak ada'
            
            # Buat kalimat deskriptif
            description = (f"SUTET {dari_gitet}-{ke_gitet} ada di wilayah {wilayah} "
                           f"dengan panjang penghantar {panjang} km dan kemampuan maksimal sebesar "
                           f"{kemampuan_max} A, {persen_derating*100} % dari nominal {nominal} A. Alasan Derating: {derating}.")
            
            # Replace the keyword in the response with the highlighted version, using re.sub for case-insensitive replacement
            description = re.sub(keyword, keyword_highlighted, description, flags=re.IGNORECASE)
            
            responses.append(description)
        
        # Tambahkan nomor pada setiap respons
        full_response = "\n".join(f"{i + 1}. {resp}" for i, resp in enumerate(responses))
        context = result.to_string(index=False)
        return context, full_response

def search_data_mitigasi(df_1, keyword):
    # Convert semua kolom dan baris ke huruf kecil untuk pencarian case-insensitive
    df_lower_ = df_1.applymap(lambda s: s.upper() if isinstance(s, str) else s)
    keyword_lower = keyword.upper()  # Konversi keyword menjadi huruf besar
    
    # Cari data yang mengandung kata kunci di salah satu kolom
    result = df_lower_[df_lower_.apply(lambda row: row.astype(str).str.contains(keyword_lower).any(), axis=1)]
    
    if result.empty:
        return None
    else:
        return result

# MITIGASI
def build_context_and_response_mitigasi(df_1, keyword):
    result = search_data_mitigasi(df_1, keyword)
    
    if result is None:
        return None, "Data tidak ditemukan untuk kata kunci yang diminta."
    else:
        # Convert the keyword to highlighted text using a span tag with background color
        keyword_highlighted = f'<span style="background-color: yellow">{keyword.upper()}</span>'
        
        # Menyusun kalimat deskriptif untuk setiap baris yang ditemukan
        responses_mitigasi = []
        for index, row in result.iterrows():
            SUTET = row.get('SUTET', 'SUTET tidak ditemukan')
            N_1 = row.get('N-1', 'Data N-1 tidak ditemukan')
            Mit_1 = row.get('Mitigasi_1', 'tidak tersedia')
            N_1_1 = row.get('N-1-1', 'tidak tersedia')
            Mit_2 = row.get('Mitigasi_2', 'tidak tersedia')
            N_1_2 = row.get('N-1-2', 'tidak tersedia')
            Mit_3 = row.get('Mitigasi_3', 'tidak tersedia')

            # Helper function to format mitigation steps and handle NaN values
            def format_mitigation(mitigation):
                if pd.isna(mitigation):
                    return "Tidak ada mitigasi yang tersedia."
                # Split each line, and add a "-" before each line to make it a bullet point.
                lines = mitigation.splitlines()
                formatted_lines = "\n".join([f"- {line.strip()}" for line in lines if line.strip()])
                return formatted_lines

            # Buat kalimat deskriptif
            description = (f"## ***{SUTET}***\n\n"
                        f"Jika terjadi gangguan di ruas **{SUTET}**, mitigasi yang harus dilakukan adalah sebagai berikut:\n\n"
                        f"**MITIGASI N-1** di ruas **{N_1}**:\n{format_mitigation(Mit_1)}\n\n"
                        f"**MITIGASI N-1-1** di ruas **{N_1_1}**:\n{format_mitigation(Mit_2)}\n\n"
                        f"**MITIGASI N-1-2** di ruas **{N_1_2}**:\n{format_mitigation(Mit_3)}")

            # Replace the keyword in the response with the highlighted version, using re.sub for case-insensitive replacement
            description = re.sub(keyword, keyword_highlighted, description, flags=re.IGNORECASE)

            # Append the description to the list
            responses_mitigasi.append(description)

        # Combine all responses into one formatted string
        full_response = "\n\n".join(responses_mitigasi)  # Use double newline for clarity between entries

        # Convert the context (dataframe) to a string without row indices
        context = result.to_string(index=False)

        return context, full_response

# Fungsi untuk mendapatkan jawaban dari model QA
def get_answer(question, context):
    # Pastikan konteks tersedia
    if context:
        result = qa_model(question=question, context=context)
        return result['answer']
    else:
        return "Data tidak ditemukan untuk kata kunci yang diminta."
