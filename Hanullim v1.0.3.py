import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
from googletrans import Translator
import openai
import pyaudio
import wave
import speech_recognition as sr
from gtts import gTTS 
import os
import pygame
import time
import numpy as np
import audioop
from colorama import init, Fore, Style 

# colorama 초기화
init()

# OpenAI API 키 설정
openai.api_key = "your api key"

# 싱할라어 -> 로마자 변환 규칙
romanization_rules = {
    'අ': 'a', 'ආ': 'ā', 'ඇ': 'æ', 'ඈ': 'ǣ', 'ඉ': 'i', 'ඊ': 'ī', 'උ': 'u', 'ඌ': 'ū',
    'එ': 'e', 'ඒ': 'ē', 'ඔ': 'o', 'ඕ': 'ō', 'ක': 'ka', 'ඛ': 'kha', 'ග': 'ga', 'ඝ': 'gha',
    'ච': 'ca', 'ඡ': 'cha', 'ජ': 'ja', 'ඣ': 'jha', 'ට': 'ṭa', 'ඨ': 'ṭha', 'ඩ': 'ḍa', 'ඪ': 'ḍha',
    'ත': 'ta', 'ථ': 'tha', 'ද': 'da', 'ධ': 'dha', 'න': 'na', 'ප': 'pa', 'ඵ': 'pha', 'බ': 'ba',
    'භ': 'bha', 'ම': 'ma', 'ය': 'ya', 'ර': 'ra', 'ල': 'la', 'ව': 'va', 'ශ': 'śa', 'ෂ': 'ṣa',
    'ස': 'sa', 'හ': 'ha', 'ළ': 'ḷa', 'ණ': 'ṇa', 'ඟ': 'ṅga', 'ඞ': 'ṅa', 'ං': 'ṁ', 'ඃ': 'ḥ',
    'ා': 'ā', 'ැ': 'æ', 'ෑ': 'ǣ', 'ි': 'i', 'ී': 'ī', 'ු': 'u', 'ූ': 'ū',
    'ෙ': 'e', 'ේ': 'ē', 'ො': 'o', 'ෝ': 'ō', '්': '',
}

# 로마자 -> 한글 발음 변환 규칙
roman_to_hangul = {
    'a': '아', 'ā': '아', 'æ': '애', 'ǣ': '애', 'i': '이', 'ī': '이', 'u': '우', 'ū': '우', 'e': '에', 
    'ē': '에', 'o': '오', 'ō': '오', 'ka': '카', 'kha': '카', 'ga': '가', 'gha': '가', 'ca': '차',
    'cha': '차', 'ja': '자', 'jha': '자', 'ṭa': '타', 'ṭha': '타', 'ḍa': '다', 'ḍha': '다',
    'ta': '타', 'tha': '타', 'da': '다', 'dha': '다', 'na': '나', 'pa': '파', 'pha': '파',
    'ba': '바', 'bha': '바', 'ma': '마', 'ya': '야', 'ra': '라', 'la': '라', 'va': '바',
    'śa': '사', 'ṣa': '사', 'sa': '사', 'ha': '하', 'ḷa': '라', 'ṇa': '나', 'ṅga': '응가',
    'ṅa': '응아', 'ṁ': '응', 'ḥ': '흐', ' ': ' ', '.': '.'
}

def is_speaking(data, threshold=1000):
    """음성 데이터에서 사용자가 말하고 있는지 감지하는 함수"""
    rms = audioop.rms(data, 2)
    return rms > threshold

def text_to_speech(text, language='si'):
    """텍스트를 음성으로 변환하여 재생하는 함수"""
    try:
        temp_file = "response.mp3"
        tts = gTTS(text=text, lang=language)
        tts.save(temp_file)
        
        pygame.mixer.init()
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        pygame.mixer.quit()
        
        try:
            os.remove(temp_file)
        except:
            pass
            
    except Exception as e:
        print(Fore.RED + f"\r❌ TTS 오류 발생: {e}" + Style.RESET_ALL)

def record_audio(filename, max_silence_time=3, sample_rate=44100, channels=2, chunk=1024):
    """동적으로 음성을 녹음하는 함수"""
    audio = pyaudio.PyAudio()
    frames = []
    silent_chunks = 0
    max_silent_chunks = int(max_silence_time * sample_rate / chunk)
    is_recording = False
    
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk
    )

    try:
        while True:
            data = stream.read(chunk)
            
            if is_speaking(data):
                if not is_recording:
                    is_recording = True
                frames.append(data)
                silent_chunks = 0
            elif is_recording:
                frames.append(data)
                silent_chunks += 1
                if silent_chunks >= max_silent_chunks:
                    break
            else:
                silent_chunks += 1
                if silent_chunks >= max_silent_chunks and not frames:
                    break

    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

        if frames:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(sample_rate)
                wf.writeframes(b''.join(frames))
            return True
        return False

def transcribe_audio(filename, language='si-LK'):
    """WAV 파일을 텍스트로 변환하는 함수"""
    recognizer = sr.Recognizer()
    
    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
    
    try:
        text = recognizer.recognize_google(audio, language=language)
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        return None
    except TypeError as e:
        return None
    
def sinhala_to_roman(text):
    """싱할라어 텍스트를 로마자로 변환하는 함수"""
    romanized_text = ""
    for char in text:
        romanized_text += romanization_rules.get(char, char)
    return romanized_text

def roman_to_korean_pronunciation(roman_text):
    """로마자를 한글 발음으로 변환하는 함수"""
    korean_pronunciation = ""
    i = 0
    while i < len(roman_text):
        if i + 1 < len(roman_text) and roman_text[i:i+2] in roman_to_hangul:
            korean_pronunciation += roman_to_hangul[roman_text[i:i+2]]
            i += 2
        else:
            korean_pronunciation += roman_to_hangul.get(roman_text[i], roman_text[i])
            i += 1
    return korean_pronunciation

# tkinter 윈도우 생성
root = tk.Tk()
root.title("to Korean Voice Translator")
root.geometry("600x600")
root.config(bg="#F0F0F0")

# 기본 메뉴 화면
def show_main_screen():
    for widget in root.winfo_children():
        widget.destroy()  # 기존 화면을 지움

    title_label = tk.Label(root, text= "to Korean Voice Translator", font=("Helvetica", 18, "bold"), bg="#F0F0F0", fg="#333")
    title_label.pack(pady=50)

    # 언어 선택 버튼들
    language_buttons_frame = tk.Frame(root, bg="#F0F0F0")
    language_buttons_frame.pack(pady=20)

    # 각 버튼 스타일
    def create_button(text, lang_code):
        return tk.Button(language_buttons_frame, text=text, font=("Helvetica", 14), bg="#4CAF50", fg="white", relief="flat", height=2, width=12, command=lambda: start_conversation(lang_code))

    burmese_button = create_button("ဗမာစာ", 'my')
    tamil_button = create_button("தமிழ்", 'ta')
    sinhala_button = create_button("සිංහල", 'si')

    burmese_button.grid(row=0, column=0, padx=15, pady=15)
    tamil_button.grid(row=0, column=1, padx=15, pady=15)
    sinhala_button.grid(row=0, column=2, padx=15, pady=15)

# 대화 화면
def start_conversation(language_code):
    for widget in root.winfo_children():
        widget.destroy()  # 기존 화면을 지움

    output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=20, font=("Helvetica", 12), bd=0, bg="#FFFFFF", fg="#333")
    output_text.grid(row=0, column=0, padx=10, pady=10)

    def process_audio():
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, "🎤 음성을 기다리는 중...\n")
        root.update()

        audio_file = "recorded_audio.wav"
        if not record_audio(audio_file):
            messagebox.showerror("Error", "음성이 감지되지 않았습니다. 다시 시도해 주세요.")
            return

        user_input = transcribe_audio(audio_file, language_code)
        if user_input:
            translated = Translator().translate(user_input, src=language_code, dest='ko')
            user_roman_text = sinhala_to_roman(user_input)
            output_text.insert(tk.END, f"\n🗣️ 사용자: {roman_to_korean_pronunciation(user_roman_text)}\n")
            output_text.insert(tk.END, f"🔍 번역: {translated.text}\n")

            try:
                output_text.insert(tk.END, "💭 응답 생성 중...\n")
                root.update()

                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "system", "content": "You are a friend to talk to. Please respond in Sinhala language."},
                              {"role": "user", "content": user_input}],
                    max_tokens=50,
                    temperature=0.3,
                )

                gpt_response = response['choices'][0]['message']['content']
                translated = Translator().translate(gpt_response, src='si', dest='ko')
                gpt_roman_text = sinhala_to_roman(gpt_response)
                
                output_text.insert(tk.END, f"\n🤖 GPT: {roman_to_korean_pronunciation(gpt_roman_text)}\n")
                output_text.insert(tk.END, f"🔍 번역: {translated.text}\n")
                output_text.insert(tk.END, "🔊 음성 재생 중...\n")
                root.update()

                text_to_speech(gpt_response)

            except Exception as e:
                messagebox.showerror("Error", f"오류 발생: {e}")
        else:
            messagebox.showerror("Error", "음성을 텍스트로 변환할 수 없습니다.")
    translator = Translator()
    go_to_menu = translator.translate("back", language_code)
    back_button = tk.Button(root, text=go_to_menu.text, font=("Helvetica", 10), bg="#FFA500", fg="white", relief="flat", height=2, width=15, command=show_main_screen)
    back_button.grid(row=1, column=0, pady=10)
    chat_start = translator.translate("start", language_code)
    start_button = tk.Button(root, text=chat_start.text, font=("Helvetica", 10), bg="#4CAF50", fg="white", relief="flat", height=2, width=15, command=process_audio)
    start_button.grid(row=2, column=0, pady=10)

# 초기 화면 표시
show_main_screen()

# tkinter 이벤트 루프 시작
root.mainloop()
