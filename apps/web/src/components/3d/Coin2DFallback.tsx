import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

interface Coin2DFallbackProps {
  change24h?: number;
}

export const Coin2DFallback: React.FC<Coin2DFallbackProps> = ({ change24h = 1.5 }) => {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const isBullish = change24h >= 0;

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setMousePos({ x, y });
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      className="relative w-72 h-72 sm:w-88 sm:h-88 md:w-96 md:h-96 flex items-center justify-center cursor-pointer select-none"
    >
      {/* Ambient Radial Glow */}
      <div
        className="absolute inset-0 rounded-full blur-3xl opacity-30 transition-colors duration-1000"
        style={{
          background: isBullish
            ? "radial-gradient(circle, rgba(245, 158, 11, 0.4) 0%, rgba(16, 185, 129, 0.2) 70%, transparent 100%)"
            : "radial-gradient(circle, rgba(245, 158, 11, 0.3) 0%, rgba(244, 63, 94, 0.25) 70%, transparent 100%)",
        }}
      />

      {/* 2D Animated Bitcoin Coin with 3D Parallax Tilt */}
      <motion.div
        animate={{
          rotateY: mousePos.x * 35,
          rotateX: -mousePos.y * 35,
        }}
        transition={{ type: "spring", stiffness: 100, damping: 15 }}
        style={{ perspective: 1000 }}
        className="relative z-10 w-56 h-56 sm:w-68 sm:h-68 md:w-72 md:h-72"
      >
        <svg
          viewBox="0 0 200 200"
          className="w-full h-full drop-shadow-[0_20px_50px_rgba(245,158,11,0.35)] animate-float"
        >
          <defs>
            {/* Gold Metallic Outer Rim */}
            <radialGradient id="goldRim" cx="30%" cy="30%" r="70%">
              <stop offset="0%" stopColor="#fef3c7" />
              <stop offset="40%" stopColor="#f59e0b" />
              <stop offset="75%" stopColor="#b45309" />
              <stop offset="100%" stopColor="#78350f" />
            </radialGradient>

            {/* Inner Face Gradient */}
            <linearGradient id="innerFace" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#fbbf24" />
              <stop offset="50%" stopColor="#d97706" />
              <stop offset="100%" stopColor="#92400e" />
            </linearGradient>

            {/* Bevel Specular Highlight */}
            <linearGradient id="specular" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Outer Edge with Milling Texture */}
          <circle cx="100" cy="100" r="96" fill="url(#goldRim)" stroke="#78350f" strokeWidth="2" />
          <circle cx="100" cy="100" r="90" fill="none" stroke="url(#specular)" strokeWidth="3" strokeDasharray="4 2" />

          {/* Coin Face */}
          <circle cx="100" cy="100" r="82" fill="url(#innerFace)" stroke="#fef3c7" strokeWidth="1.5" />
          <circle cx="100" cy="100" r="76" fill="none" stroke="#b45309" strokeWidth="1" strokeDasharray="2 4" />

          {/* Bitcoin B Symbol with Embossed Bevel */}
          <g filter="drop-shadow(0px 3px 4px rgba(0,0,0,0.6))">
            <path
              d="M 88 45 L 88 56 M 112 45 L 112 56 M 88 144 L 88 155 M 112 144 L 112 155 M 76 56 L 114 56 C 126 56 134 63 134 74 C 134 83 128 89 119 92 C 130 95 137 103 137 115 C 137 128 127 136 112 136 L 76 136 Z M 94 72 L 94 88 L 111 88 C 117 88 121 84 121 80 C 121 76 117 72 111 72 Z M 94 104 L 94 120 L 113 120 C 119 120 123 116 123 112 C 123 108 119 104 113 104 Z"
              fill="#fffbeb"
              stroke="#b45309"
              strokeWidth="2.5"
              strokeLinejoin="round"
            />
          </g>

          {/* Specular Arc Sheen */}
          <path
            d="M 30 100 A 70 70 0 0 1 170 100"
            fill="none"
            stroke="url(#specular)"
            strokeWidth="5"
            opacity="0.4"
          />
        </svg>
      </motion.div>
    </div>
  );
};
