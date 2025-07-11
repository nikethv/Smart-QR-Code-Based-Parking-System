// PWA functionality for Smart Parking System
// Handles service worker registration, installation prompts, and offline features

class PWAManager {
    constructor() {
      this.deferredPrompt = null;
      this.isOnline = navigator.onLine;
      this.offlineQueue = [];
      this.installButton = null;
      
      this.init();
    }
  
    async init() {
      console.log('PWA Manager: Initializing...');
      
      // Register service worker
      await this.registerServiceWorker();
      
      // Setup offline detection
      this.setupOfflineDetection();
      
      // Setup install prompt
      this.setupInstallPrompt();
      
      // Setup offline queue
      this.setupOfflineQueue();
      
      // Setup background sync
      this.setupBackgroundSync();
      
      // Update UI based on online status
      this.updateOnlineStatus();
      
      console.log('PWA Manager: Initialized successfully');
    }
  
    async registerServiceWorker() {
      if ('serviceWorker' in navigator) {
        try {
          const registration = await navigator.serviceWorker.register('/static/sw.js');
          console.log('Service Worker registered:', registration.scope);
          
          // Listen for service worker updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                this.showUpdateNotification();
              }
            });
          });
          
          return registration;
        } catch (error) {
          console.error('Service Worker Failed', error);
        }
      } else {
        console.log('Service Workers not supported');
      }
    }
  
    setupOfflineDetection() {
      window.addEventListener('online', () => {
        this.isOnline = true;
        this.updateOnlineStatus();
        this.processOfflineQueue();
        this.showToast('Connection restored! Syncing data...', 'success');
      });
  
      window.addEventListener('offline', () => {
        this.isOnline = false;
        this.updateOnlineStatus();
        this.showToast('You are now offline. Some features may be limited.', 'warning');
      });
    }
  
    setupInstallPrompt() {
      window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        this.deferredPrompt = e;
        this.showInstallButton();
      });
  
      window.addEventListener('appinstalled', () => {
        this.hideInstallButton();
        this.showToast('Smart Parking app installed successfully!', 'success');
        this.deferredPrompt = null;
      });
    }
  
    setupOfflineQueue() {
      // Load offline queue from localStorage
      const savedQueue = localStorage.getItem('smart-parking-offline-queue');
      if (savedQueue) {
        try {
          this.offlineQueue = JSON.parse(savedQueue);
        } catch (error) {
          console.error('Failed to load offline queue:', error);
          this.offlineQueue = [];
        }
      }
    }
  
    setupBackgroundSync() {
      if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
        console.log('Background sync supported');
      } else {
        console.log('Background sync not supported');
      }
    }
  
    updateOnlineStatus() {
      const statusIndicator = this.getOrCreateStatusIndicator();
      const body = document.body;
      
      if (this.isOnline) {
        statusIndicator.className = 'online-status online';
        statusIndicator.innerHTML = '🟢 Online';
        body.classList.remove('offline-mode');
      } else {
        statusIndicator.className = 'online-status offline';
        statusIndicator.innerHTML = '🔴 Offline';
        body.classList.add('offline-mode');
      }
    }
  
    getOrCreateStatusIndicator() {
      let indicator = document.getElementById('online-status-indicator');
      
      if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'online-status-indicator';
        indicator.className = 'online-status';
        
        // Insert after the security toggle
        const securityToggle = document.querySelector('#enhanced-security-toggle').closest('div');
        if (securityToggle) {
          securityToggle.insertAdjacentElement('afterend', indicator);
        } else {
          document.body.insertBefore(indicator, document.body.firstChild);
        }
      }
      
      return indicator;
    }
  
    showInstallButton() {
      if (!this.installButton) {
        this.installButton = document.createElement('button');
        this.installButton.className = 'install-button';
        this.installButton.innerHTML = '📱 Install App';
        this.installButton.onclick = () => this.installApp();
        
        // Insert near the top of the page
        const header = document.querySelector('h1');
        if (header) {
          header.insertAdjacentElement('afterend', this.installButton);
        }
      }
      
      this.installButton.style.display = 'block';
    }
  
    hideInstallButton() {
      if (this.installButton) {
        this.installButton.style.display = 'none';
      }
    }
  
    async installApp() {
      if (this.deferredPrompt) {
        this.deferredPrompt.prompt();
        const { outcome } = await this.deferredPrompt.userChoice;
        
        if (outcome === 'accepted') {
          console.log('User accepted the install prompt');
        } else {
          console.log('User dismissed the install prompt');
        }
        
        this.deferredPrompt = null;
      }
    }
  
    showUpdateNotification() {
      const updateBanner = document.createElement('div');
      updateBanner.className = 'update-banner';
      updateBanner.innerHTML = `
        <div class="update-content">
          <span>📱 A new version is available!</span>
          <button onclick="pwaManager.updateApp()">Update</button>
          <button onclick="this.parentElement.parentElement.remove()">Later</button>
        </div>
      `;
      
      document.body.insertBefore(updateBanner, document.body.firstChild);
    }
  
    updateApp() {
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistration().then((registration) => {
          if (registration && registration.waiting) {
            registration.waiting.postMessage({ type: 'SKIP_WAITING' });
            window.location.reload();
          }
        });
      }
    }
  
    // Offline queue management
    addToOfflineQueue(request) {
      const queueItem = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        url: request.url,
        method: request.method,
        data: request.data,
        type: request.type || 'unknown'
      };
      
      this.offlineQueue.push(queueItem);
      this.saveOfflineQueue();
      
      this.showToast(`Action saved for when you're back online`, 'info');
    }
  
    async processOfflineQueue() {
      if (this.offlineQueue.length === 0) return;
      
      console.log(`Processing ${this.offlineQueue.length} offline items...`);
      
      const processedItems = [];
      
      for (const item of this.offlineQueue) {
        try {
          const success = await this.processOfflineItem(item);
          if (success) {
            processedItems.push(item);
          }
        } catch (error) {
          console.error('Failed to process offline item:', item, error);
        }
      }
      
      // Remove processed items from queue
      this.offlineQueue = this.offlineQueue.filter(item => 
        !processedItems.find(processed => processed.id === item.id)
      );
      
      this.saveOfflineQueue();
      
      if (processedItems.length > 0) {
        this.showToast(`Synced ${processedItems.length} offline actions`, 'success');
      }
    }
  
    async processOfflineItem(item) {
      switch (item.type) {
        case 'booking':
          return await this.syncOfflineBooking(item);
        case 'release':
          return await this.syncOfflineRelease(item);
        default:
          console.log('Unknown offline item type:', item.type);
          return false;
      }
    }
  
    async syncOfflineBooking(item) {
      try {
        const response = await fetch('/send_otp', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(item.data)
        });
        
        return response.ok;
      } catch (error) {
        console.error('Failed to sync offline booking:', error);
        return false;
      }
    }
  
    async syncOfflineRelease(item) {
      try {
        const response = await fetch('/release_slot', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(item.data)
        });
        
        return response.ok;
      } catch (error) {
        console.error('Failed to sync offline release:', error);
        return false;
      }
    }
  
    saveOfflineQueue() {
      try {
        localStorage.setItem('smart-parking-offline-queue', JSON.stringify(this.offlineQueue));
      } catch (error) {
        console.error('Failed to save offline queue:', error);
      }
    }
  
    // Enhanced fetch with offline support
    async fetchWithOfflineSupport(url, options = {}, fallbackData = null) {
      if (!this.isOnline && fallbackData) {
        this.showToast('Using cached data (offline)', 'warning');
        return { ok: true, json: () => Promise.resolve(fallbackData) };
      }
      
      try {
        const response = await fetch(url, options);
        
        // Cache successful responses
        if (response.ok && options.method === 'GET') {
          this.cacheResponse(url, response.clone());
        }
        
        return response;
      } catch (error) {
        if (!this.isOnline) {
          // Try to get from cache
          const cached = await this.getCachedResponse(url);
          if (cached) {
            this.showToast('Using cached data (offline)', 'warning');
            return cached;
          }
          
          // Add to offline queue if it's a state-changing operation
          if (options.method !== 'GET') {
            this.addToOfflineQueue({
              url,
              method: options.method,
              data: options.body ? JSON.parse(options.body) : null,
              type: this.getRequestType(url)
            });
          }
        }
        
        throw error;
      }
    }
  
    async cacheResponse(url, response) {
      if ('caches' in window) {
        try {
          const cache = await caches.open('smart-parking-data-v1');
          await cache.put(url, response);
        } catch (error) {
          console.error('Failed to cache response:', error);
        }
      }
    }
  
    async getCachedResponse(url) {
      if ('caches' in window) {
        try {
          const cache = await caches.open('smart-parking-data-v1');
          return await cache.match(url);
        } catch (error) {
          console.error('Failed to get cached response:', error);
        }
      }
      return null;
    }
  
    getRequestType(url) {
      if (url.includes('/send_otp') || url.includes('/verify_otp')) return 'booking';
      if (url.includes('/release_slot')) return 'release';
      return 'unknown';
    }
  
    showToast(message, type = 'info') {
      // Use existing toast function if available
      if (window.showToast) {
        window.showToast(message, type);
      } else {
        console.log(`Toast (${type}): ${message}`);
      }
    }
  
    // Get offline capabilities status
    getOfflineStatus() {
      return {
        isOnline: this.isOnline,
        hasServiceWorker: 'serviceWorker' in navigator,
        hasCache: 'caches' in window,
        hasLocalStorage: 'localStorage' in window,
        queuedItems: this.offlineQueue.length,
        canInstall: !!this.deferredPrompt
      };
    }
  }
  
  // Initialize PWA Manager when DOM is loaded
  let pwaManager;
  
  document.addEventListener('DOMContentLoaded', () => {
    pwaManager = new PWAManager();
  });
  
  // Export for global access
  window.pwaManager = pwaManager;
  