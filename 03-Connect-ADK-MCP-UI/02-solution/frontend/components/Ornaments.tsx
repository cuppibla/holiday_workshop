import React, { useMemo, useRef, useState, useLayoutEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { TreeMode } from '../types';

interface OrnamentsProps {
  mode: TreeMode;
  count: number;
}

type OrnamentType = 'ball' | 'gift' | 'light';

interface InstanceData {
  chaosPos: THREE.Vector3;
  targetPos: THREE.Vector3;
  type: OrnamentType;
  color: THREE.Color;
  scale: number;
  speed: number;
  rotationOffset: THREE.Euler;
}

export const Ornaments: React.FC<OrnamentsProps> = ({ mode, count }) => {
  // We use 3 separate InstancedMeshes for different geometries/materials to reduce draw calls
  // but allow unique shapes.
  const ballsRef = useRef<THREE.InstancedMesh>(null);
  const giftsRef = useRef<THREE.InstancedMesh>(null);
  const lightsRef = useRef<THREE.InstancedMesh>(null);

  const dummy = useMemo(() => new THREE.Object3D(), []);

  // Generate data once
  const { ballsData, giftsData, lightsData } = useMemo(() => {
    const _balls: InstanceData[] = [];
    const _gifts: InstanceData[] = [];
    const _lights: InstanceData[] = [];

    const height = 11; // Slightly smaller than foliage
    const maxRadius = 4.5;

    // Cute / Pastel Palette
    const pink = new THREE.Color("#FF9AA2");
    const mint = new THREE.Color("#B5EAD7");
    const peach = new THREE.Color("#FFDAC1");
    const lavender = new THREE.Color("#E0BBE4");
    const babyBlue = new THREE.Color("#92A8D1");

    const palette = [pink, mint, peach, lavender, babyBlue];

    for (let i = 0; i < count; i++) {
      const rnd = Math.random();
      let type: OrnamentType = 'ball';
      if (rnd > 0.9) type = 'light';
      else if (rnd > 0.8) type = 'gift';
      // existing logic was: if (rnd > 0.8) type = 'gift'; if (rnd > 0.9) type = 'light';
      // this means > 0.9 overwrites gift with light. Correct.

      // 1. Target Position (Spiral with heavy density at bottom)
      // Use power function to bias distribution toward bottom (lower yNorm values)
      const yNorm = Math.pow(Math.random(), 2.5); // Heavy concentration at bottom
      const y = yNorm * height + 0.5;
      const rScale = (1 - yNorm);
      const theta = y * 10 + Math.random() * Math.PI * 2; // Wind around

      // Push ornaments slightly outside the foliage radius
      const r = maxRadius * rScale + (Math.random() * 0.5);

      const targetPos = new THREE.Vector3(
        r * Math.cos(theta),
        y,
        r * Math.sin(theta)
      );

      // 2. Chaos Position
      const cR = 15 + Math.random() * 15;
      const cTheta = Math.random() * Math.PI * 2;
      const cPhi = Math.acos(2 * Math.random() - 1);
      const chaosPos = new THREE.Vector3(
        cR * Math.sin(cPhi) * Math.cos(cTheta),
        cR * Math.sin(cPhi) * Math.sin(cTheta) + 5,
        cR * Math.cos(cPhi)
      );

      const scale = type === 'light' ? 0.15 : (0.2 + Math.random() * 0.25);
      const color = type === 'light' ? new THREE.Color("#FFFFAA") : palette[Math.floor(Math.random() * palette.length)];

      const data: InstanceData = {
        chaosPos,
        targetPos,
        type,
        color,
        scale,
        speed: 0.5 + Math.random() * 1.5, // Random speed for physics feel
        rotationOffset: new THREE.Euler(Math.random() * Math.PI, Math.random() * Math.PI, 0)
      };

      if (type === 'ball') _balls.push(data);
      else if (type === 'gift') _gifts.push(data);
      else _lights.push(data);
    }

    return { ballsData: _balls, giftsData: _gifts, lightsData: _lights };
  }, [count]);

  useLayoutEffect(() => {
    // Set initial colors
    [
      { ref: ballsRef, data: ballsData },
      { ref: giftsRef, data: giftsData },
      { ref: lightsRef, data: lightsData }
    ].forEach(({ ref, data }) => {
      if (ref.current) {
        data.forEach((d, i) => {
          ref.current!.setColorAt(i, d.color);
        });
        ref.current.instanceColor!.needsUpdate = true;
      }
    });
  }, [ballsData, giftsData, lightsData]);

  useFrame((state, delta) => {
    const isFormed = mode === TreeMode.FORMED;
    const time = state.clock.elapsedTime;

    // Helper to update a mesh ref
    const updateMesh = (ref: React.RefObject<THREE.InstancedMesh>, data: InstanceData[]) => {
      if (!ref.current) return;

      let needsUpdate = false;

      data.forEach((d, i) => {
        // Interpolation Factor based on individual speed and global delta
        // We use a simple approach: if formed, target is targetPos, else chaosPos
        const dest = isFormed ? d.targetPos : d.chaosPos;

        // We actually want to lerp the CURRENT position to the DESTINATION
        // But extracting current position from matrix is expensive every frame for all.
        // Instead, we calculate "current" based on a virtual progress 0-1 driven by state.

        // To simulate "physics" (heavy/light), we don't store state per particle here (too complex for this snippet).
        // Instead, we calculate position based on a time-dependent lerp factor.

        // However, a simple way to make it feel organic is:
        // Position = Mix(Chaos, Target, SmoothStep(GlobalProgress * speed))

        // Let's use a sin wave derived from time for hover, but the main transition is driven by a hidden 'progress' value
        // Since we don't have a global store for animation progress per particle, we approximate using the mode switch time.
        // For a robust system, we'd use a spring library, but here we do manual lerping.

        // Get current matrix position to lerp from? Too expensive.
        // Let's assume a global transition variable `t` that goes 0->1 or 1->0.
        // We will misuse the object's userdata or just calculate purely functional.

        // Functional approach:
        // We need an accumulated value. Let's create a visual wobble.

        // NOTE: For true interactive physics, we'd use useSprings from react-spring/three, 
        // but for 1000 instances, manual matrix manipulation is better.
        // Here we will simply interpolate between the two static positions based on a "progress" variable
        // that we track manually or approximate.

        // Let's read a custom progress from the dataset. 
        // We'll augment the data object with a mutable `currentProgress` property in a closure if possible,
        // but `data` is static.

        // Let's just use the `MathUtils.lerp` on the vectors directly inside the loop 
        // by reading the matrix, lerping, writing back.
        ref.current!.getMatrixAt(i, dummy.matrix);
        dummy.matrix.decompose(dummy.position, dummy.quaternion, dummy.scale);

        const step = delta * d.speed;
        dummy.position.lerp(dest, step);

        // Add wobble when formed
        if (isFormed && dummy.position.distanceTo(d.targetPos) < 0.5) {
          dummy.position.y += Math.sin(time * 2 + d.chaosPos.x) * 0.002;
        }

        // Rotation
        if (d.type === 'gift') {
          dummy.rotation.x += delta * 0.5;
          dummy.rotation.y += delta * 0.2;
        } else {
          // Balls face out
          dummy.lookAt(0, dummy.position.y, 0);
        }

        dummy.scale.setScalar(d.scale);
        if (d.type === 'light') {
          // Pulsate lights
          dummy.scale.multiplyScalar(1 + Math.sin(time * 5 + d.chaosPos.y) * 0.3);
        }

        dummy.updateMatrix();
        ref.current!.setMatrixAt(i, dummy.matrix);
        needsUpdate = true;
      });

      if (needsUpdate) ref.current.instanceMatrix.needsUpdate = true;
    };

    updateMesh(ballsRef, ballsData);
    updateMesh(giftsRef, giftsData);
    updateMesh(lightsRef, lightsData);
  });

  return (
    <>
      {/* Balls: Soft Pastel Spheres */}
      <instancedMesh ref={ballsRef} args={[undefined, undefined, ballsData.length]}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial
          roughness={0.4}
          metalness={0.2}
          envMapIntensity={0.8}
        />
      </instancedMesh>

      {/* Gifts: Faceted 'Jewels' or 'Candies' (Dodecahedron) */}
      <instancedMesh ref={giftsRef} args={[undefined, undefined, giftsData.length]}>
        <dodecahedronGeometry args={[1, 0]} />
        <meshStandardMaterial
          roughness={0.3}
          metalness={0.3}
          color="#white" // Tinted by instance color
        />
      </instancedMesh>

      {/* Lights: Emissive small spheres */}
      <instancedMesh ref={lightsRef} args={[undefined, undefined, lightsData.length]}>
        <sphereGeometry args={[1, 8, 8]} />
        <meshStandardMaterial
          emissive="white"
          emissiveIntensity={2}
          toneMapped={false}
          color="white" // Tinted by instance color (yellowish)
        />
      </instancedMesh>
    </>
  );
};