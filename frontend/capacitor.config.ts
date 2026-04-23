import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.filmtracker.app',
  appName: 'FilmTracker',
  webDir: 'dist',
  // Uncomment `server.url` during development for hot-reload via Android Studio.
  // Replace the IP with your machine's LAN address and ensure Vite is running.
  // server: {
  //   url: 'http://192.168.x.x:5173',
  //   cleartext: true,
  // },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
    },
  },
};

export default config;
