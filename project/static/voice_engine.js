/**
 * voice_engine.js — HoroConsultant Metaphysics AI Voice & Speech Engine (TTS / STT)
 * =================================================================================
 * Provides multi-lingual Text-to-Speech (Thai, English, Chinese) and Voice Dictation.
 */

(function (window) {
  'use strict';

  class HoroVoiceEngine {
    constructor() {
      this.synth = typeof window !== 'undefined' && 'speechSynthesis' in window ? window.speechSynthesis : null;
      this.currentUtterance = null;
      this.isPaused = false;
      this.speechRate = 1.0;
      this.activeLang = 'th';
      this.recognition = null;
      this.isListening = false;
      this.onStateChange = null;

      this.langCodeMap = {
        th: 'th-TH',
        en: 'en-US',
        zh: 'zh-CN'
      };
    }

    cleanMarkdown(text) {
      if (!text) return '';
      return text
        .replace(/[*#_~`>]/g, '')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/[-+*]\s+/g, '')
        .replace(/\|/g, ' ')
        .replace(/\n+/g, ' ')
        .trim();
    }

    getBestVoice(targetLang) {
      if (!this.synth) return null;
      const voices = this.synth.getVoices();
      const code = this.langCodeMap[targetLang] || 'th-TH';
      // Exact match
      let voice = voices.find(v => v.lang === code);
      // Prefix match
      if (!voice) {
        voice = voices.find(v => v.lang.startsWith(targetLang));
      }
      return voice || (voices.length > 0 ? voices[0] : null);
    }

    speak(text, lang = 'th', rate = 1.0, onProgress = null) {
      if (!this.synth) {
        console.warn('[HoroVoice] Web SpeechSynthesis not supported in this environment.');
        return false;
      }

      this.stop();
      const cleanText = this.cleanMarkdown(text);
      if (!cleanText) return false;

      this.activeLang = lang;
      this.speechRate = rate;

      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = this.langCodeMap[lang] || 'th-TH';
      utterance.rate = rate;
      utterance.pitch = 1.0;

      const matchedVoice = this.getBestVoice(lang);
      if (matchedVoice) {
        utterance.voice = matchedVoice;
      }

      utterance.onstart = () => {
        this.isPaused = false;
        this.notifyState('PLAYING', cleanText);
      };

      utterance.onpause = () => {
        this.isPaused = true;
        this.notifyState('PAUSED', cleanText);
      };

      utterance.onresume = () => {
        this.isPaused = false;
        this.notifyState('PLAYING', cleanText);
      };

      utterance.onend = () => {
        this.isPaused = false;
        this.currentUtterance = null;
        this.notifyState('STOPPED', '');
      };

      utterance.onerror = (err) => {
        console.warn('[HoroVoice] Speech error:', err);
        this.isPaused = false;
        this.currentUtterance = null;
        this.notifyState('STOPPED', '');
      };

      this.currentUtterance = utterance;
      this.synth.speak(utterance);
      return true;
    }

    pause() {
      if (this.synth && this.synth.speaking && !this.synth.paused) {
        this.synth.pause();
        this.isPaused = true;
        this.notifyState('PAUSED');
      }
    }

    resume() {
      if (this.synth && this.synth.paused) {
        this.synth.resume();
        this.isPaused = false;
        this.notifyState('PLAYING');
      }
    }

    stop() {
      if (this.synth) {
        this.synth.cancel();
        this.isPaused = false;
        this.currentUtterance = null;
        this.notifyState('STOPPED');
      }
    }

    setRate(rate) {
      this.speechRate = rate;
      if (this.synth && this.synth.speaking && this.currentUtterance) {
        const text = this.currentUtterance.text;
        const lang = this.activeLang;
        this.speak(text, lang, rate);
      }
    }

    notifyState(state, text = '') {
      if (typeof this.onStateChange === 'function') {
        this.onStateChange({ state, text, rate: this.speechRate, lang: this.activeLang });
      }
      this.updatePlayerUI(state, text);
    }

    updatePlayerUI(state, text = '') {
      const playerBar = document.getElementById('audio-player-bar');
      const playPauseBtn = document.getElementById('voice-play-pause-btn');
      const waveBars = document.querySelectorAll('.waveform-bar');
      const statusText = document.getElementById('voice-status-text');

      if (!playerBar) return;

      if (state === 'PLAYING') {
        playerBar.classList.remove('hidden');
        playerBar.style.display = 'flex';
        if (playPauseBtn) playPauseBtn.innerHTML = '⏸';
        waveBars.forEach(bar => bar.classList.add('animating'));
        if (statusText) statusText.textContent = 'กำลังอ่านบทพยากรณ์เสียง AI...';
      } else if (state === 'PAUSED') {
        playerBar.classList.remove('hidden');
        if (playPauseBtn) playPauseBtn.innerHTML = '▶';
        waveBars.forEach(bar => bar.classList.remove('animating'));
        if (statusText) statusText.textContent = 'หยุดชั่วคราว (Paused)';
      } else {
        playerBar.classList.add('hidden');
        playerBar.style.display = 'none';
        if (playPauseBtn) playPauseBtn.innerHTML = '▶';
        waveBars.forEach(bar => bar.classList.remove('animating'));
      }
    }

    // ====================================================================
    // 🎤 SPEECH-TO-TEXT (STT) VOICE DICTATION
    // ====================================================================

    startDictation(targetInputId = 'query', lang = 'th') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        alert('เบราว์เซอร์ของคุณยังไม่รองรับ Web Speech Recognition กรุณาใช้ Chrome หรือ Edge');
        return false;
      }

      if (this.isListening && this.recognition) {
        this.recognition.stop();
        return;
      }

      const recognition = new SpeechRecognition();
      recognition.lang = this.langCodeMap[lang] || 'th-TH';
      recognition.continuous = false;
      recognition.interimResults = true;

      const micBtn = document.getElementById('btn-voice-input');
      const targetInput = document.getElementById(targetInputId);

      recognition.onstart = () => {
        this.isListening = true;
        if (micBtn) {
          micBtn.classList.add('listening');
          micBtn.setAttribute('title', 'กำลังฟังเสียง... (คลิกเพื่อหยุด)');
        }
      };

      recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        if (targetInput) {
          targetInput.value = transcript;
        }
      };

      recognition.onerror = (event) => {
        console.warn('[HoroVoice] Recognition error:', event.error);
        this.isListening = false;
        if (micBtn) micBtn.classList.remove('listening');
      };

      recognition.onend = () => {
        this.isListening = false;
        if (micBtn) {
          micBtn.classList.remove('listening');
          micBtn.setAttribute('title', 'สั่งการด้วยเสียง (Voice Dictation)');
        }
      };

      this.recognition = recognition;
      recognition.start();
      return true;
    }
  }

  window.HoroVoice = new HoroVoiceEngine();

})(typeof window !== 'undefined' ? window : this);
