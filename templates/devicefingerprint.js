/**
 * Device Fingerprinting Library for Smart Parking System
 * Generates comprehensive device fingerprints for enhanced security
 */

class DeviceFingerprint {
    constructor() {
        this.fingerprint = null;
        this.components = {};
    }

    async generateFingerprint() {
        try {
            this.components = {
                userAgent: navigator.userAgent,
                language: navigator.language,
                languages: navigator.languages ? navigator.languages.join(',') : '',
                platform: navigator.platform,
                cookieEnabled: navigator.cookieEnabled,
                doNotTrack: navigator.doNotTrack,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                timezoneOffset: new Date().getTimezoneOffset(),
                screen: {
                    width: screen.width,
                    height: screen.height,
                    colorDepth: screen.colorDepth,
                    pixelDepth: screen.pixelDepth,
                    availWidth: screen.availWidth,
                    availHeight: screen.availHeight
                },
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                touchSupport: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
                webGL: await this.getWebGLInfo(),
                canvas: this.getCanvasFingerprint(),
                audioContext: await this.getAudioFingerprint(),
                fonts: this.getFontList(),
                plugins: this.getPluginList(),
                localStorage: this.hasLocalStorage(),
                sessionStorage: this.hasSessionStorage(),
                indexedDB: this.hasIndexedDB(),
                webRTC: await this.getWebRTCFingerprint(),
                battery: await this.getBatteryInfo(),
                connection: this.getConnectionInfo(),
                deviceMemory: navigator.deviceMemory || 'unknown',
                hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
                mediaDevices: await this.getMediaDevices(),
                permissions: await this.getPermissions(),
                webWorker: this.hasWebWorker(),
                serviceWorker: this.hasServiceWorker(),
                geolocation: this.hasGeolocation(),
                notification: this.hasNotification()
            };

            // Create a hash of all components
            const fingerprintString = JSON.stringify(this.components);
            this.fingerprint = await this.hashString(fingerprintString);
            
            return {
                fingerprint: this.fingerprint,
                components: this.components,
                timestamp: Date.now(),
                version: '1.0.0'
            };
        } catch (error) {
            console.warn('Error generating fingerprint:', error);
            return {
                fingerprint: 'error_' + Date.now(),
                components: this.components,
                timestamp: Date.now(),
                error: error.message
            };
        }
    }

    async getWebGLInfo() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (!gl) return 'unsupported';
            
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            
            return {
                vendor: gl.getParameter(gl.VENDOR),
                renderer: gl.getParameter(gl.RENDERER),
                version: gl.getParameter(gl.VERSION),
                shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
                unmaskedVendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'unknown',
                unmaskedRenderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'unknown',
                maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
                maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS)
            };
        } catch (e) {
            return 'error';
        }
    }

    getCanvasFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Set canvas size
            canvas.width = 200;
            canvas.height = 50;
            
            // Add text with different fonts and styles
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = '#069';
            ctx.fillText('Smart Parking 🚗🔍', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('Device Fingerprint', 4, 35);
            
            // Add some geometric shapes
            ctx.globalCompositeOperation = 'multiply';
            ctx.fillStyle = 'rgb(255,0,255)';
            ctx.beginPath();
            ctx.arc(50, 50, 50, 0, Math.PI * 2, true);
            ctx.closePath();
            ctx.fill();
            
            return canvas.toDataURL();
        } catch (e) {
            return 'error';
        }
    }

    async getAudioFingerprint() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const analyser = audioContext.createAnalyser();
            const gain = audioContext.createGain();
            const scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);
            
            oscillator.type = 'triangle';
            oscillator.frequency.value = 10000;
            
            gain.gain.value = 0;
            
            oscillator.connect(analyser);
            analyser.connect(scriptProcessor);
            scriptProcessor.connect(gain);
            gain.connect(audioContext.destination);
            
            oscillator.start(0);
            
            const frequencyData = new Uint8Array(analyser.frequencyBinCount);
            analyser.getByteFrequencyData(frequencyData);
            
            oscillator.stop();
            await audioContext.close();
            
            return Array.from(frequencyData).slice(0, 30).join(',');
        } catch (e) {
            return 'error';
        }
    }

    getFontList() {
        const testFonts = [
            'Arial', 'Arial Black', 'Arial Narrow', 'Arial Unicode MS',
            'Book Antiqua', 'Bookman Old Style', 'Calibri', 'Cambria',
            'Century', 'Century Gothic', 'Comic Sans MS', 'Courier',
            'Courier New', 'Garamond', 'Georgia', 'Helvetica',
            'Impact', 'Lucida Console', 'Lucida Sans Unicode',
            'Microsoft Sans Serif', 'Monotype Corsiva', 'MS Gothic',
            'MS PGothic', 'MS Reference Sans Serif', 'MS Sans Serif',
            'MS Serif', 'Palatino Linotype', 'Segoe UI', 'Symbol',
            'Tahoma', 'Times', 'Times New Roman', 'Trebuchet MS',
            'Verdana', 'Webdings', 'Wingdings'
        ];
        
        const availableFonts = [];
        const testString = 'mmmmmmmmmmlli';
        const testSize = '72px';
        
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        
        // Test baseline with a common font
        context.font = testSize + ' monospace';
        const baselineWidth = context.measureText(testString).width;
        
        testFonts.forEach(font => {
            context.font = testSize + ' ' + font + ', monospace';
            const width = context.measureText(testString).width;
            if (width !== baselineWidth) {
                availableFonts.push(font);
            }
        });
        
        return availableFonts.sort();
    }

    getPluginList() {
        const plugins = [];
        for (let i = 0; i < navigator.plugins.length; i++) {
            const plugin = navigator.plugins[i];
            plugins.push({
                name: plugin.name,
                filename: plugin.filename,
                description: plugin.description
            });
        }
        return plugins;
    }

    hasLocalStorage() {
        try {
            const test = 'test';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    hasSessionStorage() {
        try {
            const test = 'test';
            sessionStorage.setItem(test, test);
            sessionStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    hasIndexedDB() {
        return !!window.indexedDB;
    }

    async getWebRTCFingerprint() {
        try {
            const pc = new RTCPeerConnection({
                iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
            });
            
            const offer = await pc.createOffer({
                offerToReceiveAudio: true,
                offerToReceiveVideo: true
            });
            
            await pc.setLocalDescription(offer);
            
            const sdp = offer.sdp;
            pc.close();
            
            // Extract various components from SDP
            const lines = sdp.split('\n');
            const result = {
                userAgent: lines.find(line => line.includes('a=tool:')) || '',
                codecs: lines.filter(line => line.includes('a=rtpmap:')).map(line => line.split(' ')[1]).join(','),
                fingerprint: lines.find(line => line.includes('a=fingerprint:')) || ''
            };
            
            return JSON.stringify(result);
        } catch (e) {
            return 'error';
        }
    }

    async getBatteryInfo() {
        try {
            if ('getBattery' in navigator) {
                const battery = await navigator.getBattery();
                return {
                    charging: battery.charging,
                    chargingTime: battery.chargingTime,
                    dischargingTime: battery.dischargingTime,
                    level: Math.round(battery.level * 100)
                };
            }
            return 'unsupported';
        } catch (e) {
            return 'error';
        }
    }

    getConnectionInfo() {
        if ('connection' in navigator) {
            const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
            return {
                effectiveType: conn.effectiveType || 'unknown',
                downlink: conn.downlink || 'unknown',
                downlinkMax: conn.downlinkMax || 'unknown',
                rtt: conn.rtt || 'unknown',
                type: conn.type || 'unknown'
            };
        }
        return 'unsupported';
    }

    async getMediaDevices() {
        try {
            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
                const devices = await navigator.mediaDevices.enumerateDevices();
                return devices.map(device => ({
                    kind: device.kind,
                    label: device.label ? 'available' : 'permission_denied'
                }));
            }
            return 'unsupported';
        } catch (e) {
            return 'error';
        }
    }

    async getPermissions() {
        const permissions = {};
        const permissionNames = ['camera', 'microphone', 'geolocation', 'notifications'];
        
        for (const permission of permissionNames) {
            try {
                if (navigator.permissions) {
                    const result = await navigator.permissions.query({ name: permission });
                    permissions[permission] = result.state;
                } else {
                    permissions[permission] = 'unsupported';
                }
            } catch (e) {
                permissions[permission] = 'error';
            }
        }
        
        return permissions;
    }

    hasWebWorker() {
        return typeof Worker !== 'undefined';
    }

    hasServiceWorker() {
        return 'serviceWorker' in navigator;
    }

    hasGeolocation() {
        return 'geolocation' in navigator;
    }

    hasNotification() {
        return 'Notification' in window;
    }

    async hashString(str) {
        if (crypto && crypto.subtle) {
            const encoder = new TextEncoder();
            const data = encoder.encode(str);
            const hashBuffer = await crypto.subtle.digest('SHA-256', data);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        } else {
            // Fallback hash function for older browsers
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                const char = str.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash; // Convert to 32-bit integer
            }
            return Math.abs(hash).toString(16);
        }
    }
}

// Global function to get device fingerprint
window.getDeviceFingerprint = async function() {
    const fingerprinter = new DeviceFingerprint();
    return await fingerprinter.generateFingerprint();
};

// Utility function to compare two fingerprints
window.compareFingerprints = function(fp1, fp2) {
    if (!fp1 || !fp2) return 0;
    
    let matches = 0;
    let total = 0;
    
    const keys = ['userAgent', 'platform', 'screen', 'timezone', 'language'];
    
    keys.forEach(key => {
        if (fp1.components[key] && fp2.components[key]) {
            total++;
            if (JSON.stringify(fp1.components[key]) === JSON.stringify(fp2.components[key])) {
                matches++;
            }
        }
    });
    
    return total > 0 ? Math.round((matches / total) * 100) : 0;
};

console.log('Device Fingerprinting Library loaded successfully');
