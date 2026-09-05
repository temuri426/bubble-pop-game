// Animal sound system using real audio files + Web Audio synthesis
const ANIMAL_SOUNDS = {
  cat: "sounds/cat.mp3",
  dog: "sounds/dog.wav",
  lion: "sounds/lion.mp3",
  monkey: "sounds/monkey.mp3",
  frog: "sounds/frog.mp3",
  cow: "sounds/cow.wav",
  pig: "sounds/pig.mp3",
  duck: "sounds/duck.wav",
  chicken: "sounds/chicken.wav",
  sheep: "sounds/sheep.wav",
  horse: "sounds/horse.wav",
  donkey: "sounds/donkey.mp3",
  goat: "sounds/goat.wav",
  rooster: "sounds/rooster.wav",
  elephant: "sounds/elephant.mp3",
  bear: "sounds/bear.mp3",
  tiger: null,  // synthesized
  penguin: "sounds/penguin.mp3"
};

// Web Audio context for synthesis
let audioContext = null;
function getAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioContext;
}

// Synthesize tiger sound (roar/growl - noise + low frequency modulation)
function synthesizeTigerSound() {
    const ctx = getAudioContext();
    const duration = 1.0;
    
    // Noise source for breathy quality
    const bufferSize = ctx.sampleRate * duration;
    const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const noiseData = noiseBuffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
        noiseData[i] = Math.random() * 2 - 1;
    }
    const noiseSource = ctx.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    
    // Low oscillator for growl
    const osc = ctx.createOscillator();
    osc.type = 'square';
    osc.frequency.setValueAtTime(60, ctx.currentTime);
    osc.frequency.linearRampToValueAtTime(40, ctx.currentTime + duration);
    
    // Filter for noise
    const noiseFilter = ctx.createBiquadFilter();
    noiseFilter.type = 'bandpass';
    noiseFilter.frequency.value = 300;
    noiseFilter.Q.value = 5;
    
    // Filter for oscillator
    const oscFilter = ctx.createBiquadFilter();
    oscFilter.type = 'lowpass';
    oscFilter.frequency.value = 200;
    oscFilter.Q.value = 3;
    
    // Gain envelopes
    const noiseGain = ctx.createGain();
    noiseGain.gain.setValueAtTime(0.15, ctx.currentTime);
    noiseGain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);
    
    const oscGain = ctx.createGain();
    oscGain.gain.setValueAtTime(0.2, ctx.currentTime);
    oscGain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);
    
    // Master gain
    const masterGain = ctx.createGain();
    masterGain.gain.value = 0.4;
    
    noiseSource.connect(noiseFilter);
    noiseFilter.connect(noiseGain);
    noiseGain.connect(masterGain);
    
    osc.connect(oscFilter);
    oscFilter.connect(oscGain);
    oscGain.connect(masterGain);
    
    masterGain.connect(ctx.destination);
    
    noiseSource.start(ctx.currentTime);
    noiseSource.stop(ctx.currentTime + duration);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + duration);
}

// Preload audio elements for file-based sounds
const animalAudioElements = {};
const animalAudioErrors = {};

Object.keys(ANIMAL_SOUNDS).forEach(animal => {
    const src = ANIMAL_SOUNDS[animal];
    if (src) {
        const audio = new Audio(src);
        audio.preload = 'auto';
        audio.volume = 1.0;  // Maximum volume for testing
        animalAudioElements[animal] = audio;
        
        // Log any errors
        audio.addEventListener('error', (e) => {
            console.error('Audio error for', animal, ':', e);
            animalAudioErrors[animal] = e;
        }, { once: true });
        
        // Log when it can play
        audio.addEventListener('canplaythrough', () => {
            console.log('Audio ready for:', animal);
        }, { once: true });
    }
});

async function playAnimalSound(animalName) {
    console.log('playAnimalSound called with:', animalName);
    // Resume audio context on first user interaction (non-awaited, like pop sound)
    if (audioContext && audioContext.state === 'suspended') {
        try {
            audioContext.resume();
            console.log('Audio context resume called');
        } catch (e) {
            console.error('Failed to resume audio context:', e);
        }
    }
    
    // Try file-based sound first
    const audio = animalAudioElements[animalName];
    if (audio) {
        console.log('Attempting to play audio element for:', animalName);
        try {
            audio.currentTime = 0;
            const playPromise = audio.play();
            if (playPromise !== undefined) {
                await playPromise;
                console.log('Successfully played:', animalName);
            }
        } catch (e) {
            console.error('Audio play failed for', animalName, ':', e);
        }
        return;
    }
    
    // Fallback to synthesis (tiger only)
    if (animalName === 'tiger') {
        console.log('Playing synthesized tiger sound');
        synthesizeTigerSound();
        return;
    }
    
    console.log('No sound for:', animalName);
}

// Resume audio context on user interaction (required by browsers)
document.addEventListener('click', () => {
    console.log('Document click received');
    if (audioContext && audioContext.state === 'suspended') {
        try {
            audioContext.resume();
            console.log('Audio context resumed via click');
        } catch (e) {
            console.error('Failed to resume audio context on click:', e);
        }
    }
}, { once: true });

// Also resume on touchstart for mobile
document.addEventListener('touchstart', () => {
    console.log('Document touchstart received');
    if (audioContext && audioContext.state === 'suspended') {
        try {
            audioContext.resume();
            console.log('Audio context resumed via touchstart');
        } catch (e) {
            console.error('Failed to resume audio context on touchstart:', e);
        }
    }
}, { once: true });

// Export for use in main game
window.playAnimalSound = playAnimalSound;
console.log('Animal sound system loaded, animals:', Object.keys(ANIMAL_SOUNDS).filter(a => ANIMAL_SOUNDS[a]));