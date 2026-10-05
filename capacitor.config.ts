import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.moveamind.app',
  appName: 'Move A Mind',
  webDir: 'web',
  server: {
    url: 'https://move-a-mind-v08-production.up.railway.app',
    cleartext: false
  }
};

export default config;
