import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { TreeMode } from '../types';

interface TreeStarProps {
  mode: TreeMode;
}

export const TreeStar: React.FC<TreeStarProps> = ({ mode }) => {
  const starRef = useRef<THREE.Group>(null);
  const lightRef = useRef<THREE.PointLight>(null);

  // Create a 5-pointed star shape
  const starShape = React.useMemo(() => {
    const shape = new THREE.Shape();
    const outerRadius = 0.8; // Larger star
    const innerRadius = 0.32;
    const points = 5;

    for (let i = 0; i < points * 2; i++) {
      const angle = (i * Math.PI) / points - Math.PI / 2;
      const radius = i % 2 === 0 ? outerRadius : innerRadius;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;

      if (i === 0) {
        shape.moveTo(x, y);
      } else {
        shape.lineTo(x, y);
      }
    }
    shape.closePath();

    return shape;
  }, []);

  const extrudeSettings = {
    depth: 0.15,
    bevelEnabled: true,
    bevelThickness: 0.08,
    bevelSize: 0.08,
    bevelSegments: 3,
  };

  // Target positions
  const formedPos = new THREE.Vector3(0, 13, 0); // Higher above tree (height ~11)
  const chaosPos = new THREE.Vector3(
    Math.random() * 20 - 10,
    15 + Math.random() * 10,
    Math.random() * 20 - 10
  );

  useFrame((state, delta) => {
    if (!starRef.current) return;

    const isFormed = mode === TreeMode.FORMED;
    const time = state.clock.elapsedTime;

    // Position animation
    const targetPos = isFormed ? formedPos : chaosPos;
    starRef.current.position.lerp(targetPos, delta * 1.5);

    // Rotation animation
    if (isFormed) {
      // Gentle rotation and floating when formed
      starRef.current.rotation.z = time * 0.5;
      starRef.current.position.y = 13 + Math.sin(time * 2) * 0.1;
    } else {
      // Spinning in chaos mode
      starRef.current.rotation.x += delta * 2;
      starRef.current.rotation.y += delta * 3;
    }

    // Pulsating light
    if (lightRef.current) {
      const pulse = 2 + Math.sin(time * 3) * 0.5;
      lightRef.current.intensity = pulse;
    }
  });

  return (
    <group ref={starRef} position={[0, 13, 0]}>
      {/* Star Mesh */}
      <mesh rotation={[0, 0, 0]}>
        <extrudeGeometry args={[starShape, extrudeSettings]} />
        <meshStandardMaterial
          color="#FDFD96"
          emissive="#FFFFAA"
          emissiveIntensity={2}
          metalness={0.4}
          roughness={0.3}
          toneMapped={false}
        />
      </mesh>

      {/* Point Light for glow effect */}
      <pointLight
        ref={lightRef}
        color="#FDFD96"
        intensity={2}
        distance={5}
        decay={2}
      />
    </group>
  );
};

