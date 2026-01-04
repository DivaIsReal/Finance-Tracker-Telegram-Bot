import re
import os
from google.cloud import vision
from typing import Optional, Dict
from datetime import datetime

class OCRProcessor:
    """Processor untuk OCR struk menggunakan Google Cloud Vision API"""
    
    def __init__(self):
        try:
            # Set credentials dari file yang sama dengan Google Sheets
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credentials.json'
            
            # Initialize Vision API client
            self.client = vision.ImageAnnotatorClient()
            self.connected = True
            print("✅ Google Cloud Vision API terhubung!")
            
        except Exception as e:
            print(f"❌ Error koneksi Vision API: {e}")
            print("⚠️  Pastikan Cloud Vision API sudah di-enable di Google Cloud Console")
            self.connected = False
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text dari image menggunakan Google Cloud Vision API
        """
        if not self.connected:
            return ""
        
        try:
            # Read image file
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            # Prepare image for Vision API
            image = vision.Image(content=content)
            
            # Detect text dengan Vision API
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            
            if response.error.message:
                raise Exception(response.error.message)
            
            # Ambil full text (index 0 = full text, sisanya per word)
            if texts:
                full_text = texts[0].description
                print(f"📝 Vision OCR Result:\n{full_text}\n")
                return full_text
            
            return ""
            
        except Exception as e:
            print(f"❌ Error OCR: {e}")
            return ""
    
    def extract_amount(self, text: str) -> Optional[float]:
        """
        Extract nominal uang dari text OCR
        Support berbagai format angka Indonesia
        """
        # Remove whitespace berlebih
        text = ' '.join(text.split())
        text_lower = text.lower()
        
        # Pattern untuk mencari total/jumlah
        patterns = [
            # Total dengan label (prioritas tertinggi)
            r'(?:^|\n)total[\s:]*(?:rp)?[\s.,]*(\d+[\d.,]*)',
            r'(?:grand\s*total|jumlah|bayar)[\s:]*(?:rp)?[\s.,]*(\d+[\d.,]*)',
            # Rp dengan angka
            r'rp[\s.,]*(\d+[\d.,]*)',
            # Angka dengan separator ribuan (titik atau koma)
            r'(\d{1,3}(?:[.,]\d{3})+)',
            # Angka biasa di atas 1000
            r'\b(\d{4,})\b',
        ]
        
        amounts = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Clean: hapus separator ribuan
                clean = match.replace('.', '').replace(',', '')
                try:
                    amount = float(clean)
                    # Filter: minimal 1000, maksimal 100jt
                    if 1000 <= amount <= 100_000_000:
                        amounts.append(amount)
                except:
                    continue
        
        # Return angka terbesar (biasanya total)
        if amounts:
            amounts.sort(reverse=True)
            return amounts[0]
        
        return None
    
    def extract_merchant(self, text: str) -> str:
        """
        Extract nama merchant/toko dari text
        Biasanya di baris pertama atau yang paling menonjol
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            return "Merchant"
        
        # Filter baris yang kemungkinan nama toko
        candidates = []
        
        for line in lines[:5]:  # Cek 5 baris pertama
            # Skip jika ada terlalu banyak angka
            digit_count = len(re.findall(r'\d', line))
            if digit_count > len(line) * 0.4:
                continue
            
            # Skip jika terlalu pendek atau panjang
            if not (3 <= len(line) <= 50):
                continue
            
            # Skip keyword yang bukan nama toko
            skip_keywords = ['jalan', 'jl.', 'jln', 'telp', 'hp', 'phone', 
                           'email', '@', 'tanggal', 'date', 'alamat', 'address',
                           'receipt', 'struk', 'nota', 'bill', 'invoice', 'dine']
            if any(kw in line.lower() for kw in skip_keywords):
                continue
            
            candidates.append(line)
        
        return candidates[0] if candidates else "Merchant"
    
    def extract_date(self, text: str) -> Optional[datetime]:
        """
        Extract tanggal dari struk
        Support berbagai format tanggal Indonesia & Internasional
        """
        # Pattern untuk berbagai format tanggal
        date_patterns = [
            # DD/MM/YYYY, DD-MM-YYYY
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'dmy'),
            # DD/MM/YY, DD-MM-YY
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})\b', 'dmy2'),
            # YYYY-MM-DD, YYYY/MM/DD
            (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', 'ymd'),
            # DD Mon YYYY (25 Dec 2024, 25 Des 2024, Oct 23 2023)
            (r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|des|agu|okt)\w*\s+(\d{4})', 'dmy_text'),
            (r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|des|agu|okt)\w*\s+(\d{1,2})\s+(\d{4})', 'mdy_text'),
        ]
        
        for pattern, format_type in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if format_type == 'dmy':
                        day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day))
                    elif format_type == 'dmy2':
                        day, month, year = match.groups()
                        year = int(year)
                        year = 2000 + year if year < 100 else year
                        return datetime(year, int(month), int(day))
                    elif format_type == 'ymd':
                        year, month, day = match.groups()
                        return datetime(int(year), int(month), int(day))
                    elif format_type == 'dmy_text':
                        day, month_str, year = match.groups()
                        months = {
                            'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6,
                            'jul':7, 'aug':8, 'agu':8, 'sep':9, 'oct':10, 'okt':10,
                            'nov':11, 'dec':12, 'des':12
                        }
                        month = months.get(month_str[:3].lower())
                        if month:
                            return datetime(int(year), month, int(day))
                    elif format_type == 'mdy_text':
                        month_str, day, year = match.groups()
                        months = {
                            'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6,
                            'jul':7, 'aug':8, 'agu':8, 'sep':9, 'oct':10, 'okt':10,
                            'nov':11, 'dec':12, 'des':12
                        }
                        month = months.get(month_str[:3].lower())
                        if month:
                            return datetime(int(year), month, int(day))
                except:
                    continue
        
        return None
    
    def detect_category_from_merchant(self, merchant: str) -> str:
        """
        Deteksi kategori dari nama merchant
        Support merchant Indonesia
        """
        merchant_lower = merchant.lower()
        
        # Merchant keywords untuk kategori
        category_keywords = {
            'Makan': [
                # Restaurant chains
                'resto', 'restaurant', 'cafe', 'warung', 'makan', 'food', 
                'kfc', 'mcd', 'mcdonald', 'pizza', 'burger', 'wendys',
                'hoka', 'yoshinoya', 'hokben', 'solaria', 'breadtalk',
                'starbucks', 'janji jiwa', 'kopi', 'coffee', 'kedai',
                'master chef', 'chef',
                # Food types
                'bakso', 'mie', 'nasi', 'ayam', 'soto', 'sate', 'gado',
                'padang', 'seafood', 'dapur', 'kitchen', 'catering'
            ],
            'Belanja': [
                'mart', 'market', 'supermarket', 'indomaret', 'alfamart', 
                'minimarket', 'hypermart', 'lottemart', 'carrefour', 'giant',
                'shopee', 'tokopedia', 'lazada', 'blibli', 'bukalapak',
                'store', 'shop', 'toko', 'mall', 'plaza'
            ],
            'Transport': [
                'grab', 'gojek', 'uber', 'maxim', 'blue bird', 'bluebird',
                'taxi', 'taksi', 'ojek', 'spbu', 'pertamina', 'shell', 
                'total', 'bensin', 'parkir', 'parking', 'toll', 'tol'
            ],
            'Kesehatan': [
                'apotek', 'pharmacy', 'apotik', 'rumah sakit', 'rs', 'hospital',
                'klinik', 'clinic', 'guardian', 'century', 'kimia farma',
                'viva health', 'dokter', 'medical', 'medis', 'lab', 'laboratorium'
            ],
            'Hiburan': [
                'cinema', 'bioskop', 'xxi', 'cgv', 'cinepolis',
                'gym', 'fitness', 'karaoke', 'timezone', 
                'amazone', 'waterboom', 'theme park', 'taman'
            ],
            'Tagihan': [
                'listrik', 'pln', 'token', 'telkom', 'indihome',
                'xl', 'telkomsel', 'axis', 'three', 'smartfren',
                'pulsa', 'pdam', 'air'
            ]
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in merchant_lower:
                    return category
        
        return 'Lainnya'
    
    def format_detail_text(self, raw_text: str, max_lines: int = 30) -> str:
        """
        Format raw text OCR menjadi detail yang lebih rapi
        Ambil max_lines baris pertama yang relevan
        """
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        
        # Filter baris yang terlalu pendek (< 2 karakter)
        filtered = [line for line in lines if len(line) >= 2]
        
        # Ambil max_lines baris pertama
        detail_lines = filtered[:max_lines]
        
        # Join dengan newline
        return '\n'.join(detail_lines)
    
    def process_receipt(self, image_path: str) -> Dict:
        """
        Process receipt image dan extract semua info menggunakan Google Vision API
        """
        if not self.connected:
            return {
                'success': False,
                'error': 'Google Cloud Vision API tidak terhubung. Pastikan API sudah di-enable!'
            }
        
        # Extract text dari image
        text = self.extract_text_from_image(image_path)
        
        if not text:
            return {
                'success': False,
                'error': 'Tidak bisa membaca text dari image. Pastikan foto jelas dan ada tulisan!'
            }
        
        # Extract informasi
        amount = self.extract_amount(text)
        merchant = self.extract_merchant(text)
        category = self.detect_category_from_merchant(merchant)
        date = self.extract_date(text)
        detail = self.format_detail_text(text)
        
        return {
            'success': True,
            'amount': amount,
            'merchant': merchant,
            'category': category,
            'date': date or datetime.now(),
            'detail': detail,
            'raw_text': text
        }


# Singleton instance
ocr_processor = OCRProcessor()