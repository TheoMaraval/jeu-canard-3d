import { defineConfig } from 'vite';

// Les fichiers produits par le pipeline Blender (assets/) sont servis à la racine :
// props.glb, scenes.json, scenes/<ville>/quartier.glb, scenes/<ville>/placements.json.
export default defineConfig({
  base: './',
  publicDir: '../assets',
  server: { port: 5173, strictPort: true },
  test: { include: ['tests/**/*.test.js'] },
});
