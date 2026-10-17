import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface CoinScene3DProps {
  change24h?: number;
}

export const CoinScene3D: React.FC<CoinScene3DProps> = ({ change24h = 1.25 }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const isBullish = change24h >= 0;

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 400;
    const height = container.clientHeight || 400;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.z = 6.2;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // 2. Dynamic Texture for Coin Face (Bitcoin Symbol & Rim)
    const canvas = document.createElement("canvas");
    canvas.width = 1024;
    canvas.height = 1024;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      // Golden radial background
      const grad = ctx.createRadialGradient(512, 512, 100, 512, 512, 500);
      grad.addColorStop(0, "#fbbf24");
      grad.addColorStop(0.6, "#d97706");
      grad.addColorStop(1, "#78350f");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 1024, 1024);

      // Outer rings
      ctx.strokeStyle = "#fef3c7";
      ctx.lineWidth = 16;
      ctx.beginPath();
      ctx.arc(512, 512, 480, 0, Math.PI * 2);
      ctx.stroke();

      ctx.strokeStyle = "#92400e";
      ctx.lineWidth = 8;
      ctx.setLineDash([12, 12]);
      ctx.beginPath();
      ctx.arc(512, 512, 450, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);

      // Bitcoin Symbol
      ctx.fillStyle = "#fffbeb";
      ctx.strokeStyle = "#78350f";
      ctx.lineWidth = 14;
      ctx.font = "bold 520px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.strokeText("₿", 512, 530);
      ctx.fillText("₿", 512, 530);
    }

    const faceTexture = new THREE.CanvasTexture(canvas);
    faceTexture.anisotropy = 8;

    // 3. Materials
    const goldSideMaterial = new THREE.MeshStandardMaterial({
      color: new THREE.Color("#d97706"),
      metalness: 0.94,
      roughness: 0.22,
    });

    const goldFaceMaterial = new THREE.MeshStandardMaterial({
      map: faceTexture,
      metalness: 0.95,
      roughness: 0.18,
    });

    // Mesh with materials: [side, top/face, bottom/back]
    const coinGeometry = new THREE.CylinderGeometry(2.0, 2.0, 0.28, 64);
    const coin = new THREE.Mesh(coinGeometry, [
      goldSideMaterial,
      goldFaceMaterial,
      goldFaceMaterial,
    ]);
    coin.rotation.x = Math.PI / 2.2;
    scene.add(coin);

    // 4. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xfffaed, 2.2);
    dirLight1.position.set(5, 8, 6);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xf59e0b, 1.4);
    dirLight2.position.set(-6, -4, 4);
    scene.add(dirLight2);

    // Dynamic backlight responding to 24h change
    const tintColor = isBullish ? 0x10b981 : 0xf43f5e;
    const rimLight = new THREE.PointLight(tintColor, 3.5, 10);
    rimLight.position.set(0, -2, -3);
    scene.add(rimLight);

    // 5. GPU Particles
    const particleCount = 280;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    const particleColors = new Float32Array(particleCount * 3);

    const pColor = new THREE.Color(isBullish ? "#10b981" : "#f43f5e");
    const goldColor = new THREE.Color("#f59e0b");

    for (let i = 0; i < particleCount; i++) {
      particlePositions[i * 3] = (Math.random() - 0.5) * 12;
      particlePositions[i * 3 + 1] = (Math.random() - 0.5) * 12;
      particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 8;

      const mix = Math.random();
      const col = goldColor.clone().lerp(pColor, mix * 0.7);
      particleColors[i * 3] = col.r;
      particleColors[i * 3 + 1] = col.g;
      particleColors[i * 3 + 2] = col.b;
    }

    particleGeo.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));
    particleGeo.setAttribute("color", new THREE.BufferAttribute(particleColors, 3));

    const particleMat = new THREE.PointsMaterial({
      size: 0.045,
      vertexColors: true,
      transparent: true,
      opacity: 0.65,
      blending: THREE.AdditiveBlending,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // 6. Interaction & Animation Loop
    let mouseX = 0;
    let mouseY = 0;
    let targetRotationX = Math.PI / 2.2;
    let targetRotationY = 0;

    const onPointerMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
    };

    window.addEventListener("mousemove", onPointerMove);

    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Continuous subtle coin float & slow idle rotation
      const scrollY = window.scrollY || 0;
      const scrollProgress = Math.min(scrollY / 800, 1.5);

      targetRotationY = elapsedTime * 0.45 + mouseX * 0.6 + scrollProgress * Math.PI;
      targetRotationX = Math.PI / 2.2 - mouseY * 0.4 + scrollProgress * 0.4;

      coin.rotation.y += (targetRotationY - coin.rotation.y) * 0.05;
      coin.rotation.x += (targetRotationX - coin.rotation.x) * 0.05;
      coin.position.y = Math.sin(elapsedTime * 1.5) * 0.08 - scrollProgress * 0.3;

      // Particle subtle rotation
      particles.rotation.y = elapsedTime * 0.04;

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("mousemove", onPointerMove);
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
      faceTexture.dispose();
      coinGeometry.dispose();
      goldFaceMaterial.dispose();
      goldSideMaterial.dispose();
      particleGeo.dispose();
      particleMat.dispose();
    };
  }, [change24h, isBullish]);

  return <div ref={mountRef} className="w-full h-full min-h-[360px] flex items-center justify-center cursor-grab" />;
};
