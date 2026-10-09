const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

// When deploying specific apps (like web/admin) in a monorepo, 
// other apps' dependencies (like expo-av for mobile) aren't installed.
// The default patch-package halts the entire build if a patched package is missing.

const patchesDir = path.join(__dirname, '..', 'patches');
if (!fs.existsSync(patchesDir)) {
  process.exit(0);
}

const patches = fs.readdirSync(patchesDir).filter(f => f.endsWith('.patch'));
let missingPackages = false;

for (const patch of patches) {
  // Extract package name from patch file (e.g. "expo-av+16.0.8.patch" -> "expo-av")
  // Handles scoped packages: "@react-navigation+native+7.1.33.patch" -> "@react-navigation/native"
  const pkgNameStr = patch.split('+').slice(0, -1).join('/');
  
  if (!pkgNameStr) continue;
  
  // Convert standard package name back from patch format
  const pkgName = pkgNameStr.startsWith('@') 
    ? pkgNameStr.replace(/^(@[^\/]+)\/+/, '$1/')
    : pkgNameStr.split('/')[0];
    
  const nodeModulesPath = path.join(__dirname, '..', 'node_modules', pkgName);
  
  if (!fs.existsSync(nodeModulesPath)) {
    console.log(`\n[postinstall] Skipping patches - ${pkgName} is not installed (likely a partial workspace install).`);
    missingPackages = true;
    break;
  }
}

try {
  if (missingPackages) {
    console.log('[postinstall] Exiting gracefully without breaking the build.\n');
  } else {
    execSync('npx patch-package', { stdio: 'inherit', cwd: path.join(__dirname, '..') });
  }
} catch (e) {
  // If patch-package itself fails for a valid install, log but don't hard crash Vercel
  console.error('[postinstall] patch-package warning:', e.message);
  // Re-throw if not on Vercel so local devs catch bad patches
  if (!process.env.VERCEL) {
    process.exit(1);
  }
}
