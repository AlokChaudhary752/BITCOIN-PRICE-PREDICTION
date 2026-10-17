import React, { Suspense, lazy, useState, useEffect } from "react";
import { Coin2DFallback } from "./Coin2DFallback";

const CoinScene3D = lazy(() =>
  import("./CoinScene3D").then((m) => ({ default: m.CoinScene3D }))
);

interface HeroCoinProps {
  change24h?: number;
}

export const HeroCoin: React.FC<HeroCoinProps> = ({ change24h = 1.25 }) => {
  const [canRender3D, setCanRender3D] = useState<boolean>(false);
  const [checked, setChecked] = useState<boolean>(false);

  useEffect(() => {
    // Detect WebGL support and screen width for performance budgeting
    try {
      const canvas = document.createElement("canvas");
      const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
      const isLargeScreen = window.innerWidth >= 768;
      const isTouchDevice = "ontouchstart" in window || navigator.maxTouchPoints > 2;

      // Enable full 3D scene on desktop with WebGL
      if (gl && isLargeScreen && !isTouchDevice) {
        setCanRender3D(true);
      } else {
        setCanRender3D(false);
      }
    } catch {
      setCanRender3D(false);
    } finally {
      setChecked(true);
    }
  }, []);

  if (!checked) {
    return <Coin2DFallback change24h={change24h} />;
  }

  if (canRender3D) {
    return (
      <Suspense fallback={<Coin2DFallback change24h={change24h} />}>
        <div className="w-full h-80 sm:h-96 md:h-[450px]">
          <CoinScene3D change24h={change24h} />
        </div>
      </Suspense>
    );
  }

  return <Coin2DFallback change24h={change24h} />;
};
