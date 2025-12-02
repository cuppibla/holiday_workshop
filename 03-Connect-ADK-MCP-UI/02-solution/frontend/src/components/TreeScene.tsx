import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sparkles, Float, Stars, RoundedBox } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import * as THREE from 'three';

// --- Components ---

const Garland = () => {
    const curve = useMemo(() => {
        const points = [];
        const turns = 6;
        const height = 4.5;
        const radiusBase = 1.6;

        for (let i = 0; i <= 120; i++) {
            const t = i / 120;
            const angle = t * Math.PI * 2 * turns;
            const y = t * height - 1.8;
            const r = radiusBase * (1 - t) + 0.2;
            points.push(new THREE.Vector3(Math.cos(angle) * r, y, Math.sin(angle) * r));
        }
        return new THREE.CatmullRomCurve3(points);
    }, []);

    return (
        <mesh position={[0, 0.5, 0]} castShadow>
            <tubeGeometry args={[curve, 120, 0.06, 8, false]} />
            <meshStandardMaterial color="#c0c0c0" metalness={0.9} roughness={0.1} />
        </mesh>
    );
};

// Detailed Procedural Tree Component
const Tree = ({ treeState }: { treeState: any }) => {
    const group = useRef<THREE.Group>(null);

    // High detail layers
    const layers = useMemo(() => {
        const l = [];
        const count = 10;
        for (let i = 0; i < count; i++) {
            const t = i / (count - 1);
            l.push({
                y: 0.5 + i * 0.55,
                scale: 1.8 * (1 - t) + 0.2,
                segments: 12 + Math.floor((1 - t) * 6)
            });
        }
        return l;
    }, []);

    const lightsColor = treeState?.lights_color === 'warm_white' ? '#ffebcd' :
        treeState?.lights_color === 'red' ? '#ff0000' :
            treeState?.lights_color === 'blue' ? '#0000ff' : '#ffebcd';

    const ornamentColor = treeState?.theme === 'emerald_gold' ? '#ffd700' : '#c0c0c0';

    useFrame((state) => {
        if (group.current) {
            group.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.1) * 0.03;
        }
    });

    return (
        <group ref={group} position={[0, -2.5, 0]}>
            {/* Trunk */}
            <mesh position={[0, 1, 0]} castShadow receiveShadow>
                <cylinderGeometry args={[0.35, 0.6, 2.5, 10]} />
                <meshStandardMaterial color="#3e2723" roughness={0.9} />
            </mesh>

            {/* Leaves - Dense and detailed */}
            {layers.map((layer, i) => (
                <group key={i} position={[0, layer.y + 0.8, 0]}>
                    <mesh castShadow receiveShadow>
                        <coneGeometry args={[layer.scale, 1.1, layer.segments]} />
                        <meshStandardMaterial
                            color="#1a8c46"
                            roughness={0.6}
                            metalness={0.1}
                        />
                    </mesh>
                    {/* Inner volume layer */}
                    <mesh scale={[0.92, 0.95, 0.92]} position={[0, -0.05, 0]}>
                        <coneGeometry args={[layer.scale, 1.1, layer.segments]} />
                        <meshStandardMaterial color="#0f5132" roughness={0.9} />
                    </mesh>
                </group>
            ))}

            {/* Ornaments - Varied and plentiful */}
            {layers.map((layer, i) => {
                if (i === layers.length - 1) return null;
                const count = 8 + i;
                return (
                    <group key={`ornaments-${i}`} position={[0, layer.y + 0.6, 0]}>
                        {[...Array(count)].map((_, j) => {
                            const angle = (j / count) * Math.PI * 2 + i * 0.5;
                            const radius = layer.scale * 0.9;
                            const type = (i + j) % 3;

                            return (
                                <mesh key={j} position={[Math.cos(angle) * radius, -0.15, Math.sin(angle) * radius]} castShadow>
                                    {type === 0 ? <sphereGeometry args={[0.1, 16, 16]} /> :
                                        type === 1 ? <dodecahedronGeometry args={[0.09]} /> :
                                            <sphereGeometry args={[0.08, 16, 16]} />}
                                    <meshStandardMaterial
                                        color={type === 2 ? '#ff0000' : ornamentColor}
                                        metalness={0.8}
                                        roughness={0.1}
                                    />
                                </mesh>
                            );
                        })}
                    </group>
                );
            })}

            {/* Fairy Lights - Dense Spiral */}
            <group>
                {[...Array(100)].map((_, i) => {
                    const t = i / 100;
                    const y = t * 5 + 0.5;
                    const radius = (1 - t) * 1.7 + 0.15;
                    const angle = t * Math.PI * 14;
                    return (
                        <mesh key={`light-${i}`} position={[Math.cos(angle) * radius, y, Math.sin(angle) * radius]}>
                            <sphereGeometry args={[0.04, 8, 8]} />
                            <meshStandardMaterial color={lightsColor} emissive={lightsColor} emissiveIntensity={3} toneMapped={false} />
                        </mesh>
                    )
                })}
            </group>

            <Garland />

            {/* Snow on tree */}
            <Sparkles count={80} scale={4} size={3} speed={0.4} opacity={0.5} color="#fff" position={[0, 3, 0]} />
        </group>
    );
};

// Floating background items - Gifts, Candy, Candy Canes
const RoamingItems = () => {
    const items = useMemo(() => {
        return [...Array(20)].map((_, i) => ({
            pos: [
                (Math.random() - 0.5) * 22,
                Math.random() * 10 - 2,
                (Math.random() - 0.5) * 20 - 5
            ],
            rot: [Math.random() * Math.PI, Math.random() * Math.PI, 0],
            scale: 0.6 + Math.random() * 0.6, // Slightly larger
            type: ['gift', 'gift', 'candy', 'candy', 'cane'][Math.floor(Math.random() * 5)],
            color: ['#ef4444', '#22c55e', '#3b82f6', '#eab308', '#a855f7'][Math.floor(Math.random() * 5)],
            ribbonColor: '#ffffff',
            speed: 0.4 + Math.random() * 0.6
        }));
    }, []);

    return (
        <group>
            {items.map((data, i) => (
                <Float key={i} speed={data.speed} rotationIntensity={1} floatIntensity={2} floatingRange={[-1, 1]}>
                    <group position={data.pos as [number, number, number]} rotation={data.rot as [number, number, number]}>

                        {/* GIFT BOX */}
                        {data.type === 'gift' && (
                            <group>
                                <RoundedBox args={[data.scale, data.scale, data.scale]} radius={0.05} smoothness={4} castShadow receiveShadow>
                                    <meshStandardMaterial color={data.color} roughness={0.3} metalness={0.1} />
                                </RoundedBox>
                                <mesh scale={[1.02, 1, 0.2]}>
                                    <boxGeometry args={[data.scale, data.scale, data.scale]} />
                                    <meshStandardMaterial color={data.ribbonColor} />
                                </mesh>
                                <mesh scale={[0.2, 1, 1.02]}>
                                    <boxGeometry args={[data.scale, data.scale, data.scale]} />
                                    <meshStandardMaterial color={data.ribbonColor} />
                                </mesh>
                                {/* Bow */}
                                <group position={[0, data.scale / 2, 0]}>
                                    <mesh position={[0.1, 0.1, 0]} rotation={[0, 0, -Math.PI / 4]}>
                                        <torusGeometry args={[0.1 * data.scale, 0.04 * data.scale, 8, 16]} />
                                        <meshStandardMaterial color={data.ribbonColor} />
                                    </mesh>
                                    <mesh position={[-0.1, 0.1, 0]} rotation={[0, 0, Math.PI / 4]}>
                                        <torusGeometry args={[0.1 * data.scale, 0.04 * data.scale, 8, 16]} />
                                        <meshStandardMaterial color={data.ribbonColor} />
                                    </mesh>
                                </group>
                            </group>
                        )}

                        {/* WRAPPED CANDY - Larger and distinct */}
                        {data.type === 'candy' && (
                            <group>
                                {/* Center */}
                                <mesh castShadow rotation={[0, 0, Math.PI / 2]}>
                                    <cylinderGeometry args={[data.scale * 0.3, data.scale * 0.3, data.scale * 0.8, 16]} />
                                    <meshStandardMaterial color={data.color} roughness={0.2} metalness={0.3} />
                                </mesh>
                                {/* Wrappers */}
                                <mesh position={[data.scale * 0.55, 0, 0]} rotation={[0, 0, -Math.PI / 2]}>
                                    <coneGeometry args={[data.scale * 0.3, data.scale * 0.4, 16]} />
                                    <meshStandardMaterial color="#ffffff" roughness={0.4} />
                                </mesh>
                                <mesh position={[-data.scale * 0.55, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
                                    <coneGeometry args={[data.scale * 0.3, data.scale * 0.4, 16]} />
                                    <meshStandardMaterial color="#ffffff" roughness={0.4} />
                                </mesh>
                            </group>
                        )}

                        {/* CANDY CANE */}
                        {data.type === 'cane' && (
                            <group>
                                {/* Stick */}
                                <mesh position={[0, 0, 0]}>
                                    <cylinderGeometry args={[data.scale * 0.1, data.scale * 0.1, data.scale * 1.2, 16]} />
                                    <meshStandardMaterial color="#ef4444" roughness={0.2} />
                                </mesh>
                                {/* Hook */}
                                <mesh position={[data.scale * 0.2, data.scale * 0.6, 0]} rotation={[0, 0, 0]}>
                                    <torusGeometry args={[data.scale * 0.2, data.scale * 0.1, 8, 16, Math.PI]} />
                                    <meshStandardMaterial color="#ef4444" roughness={0.2} />
                                </mesh>
                                {/* White Stripes (Simplified as rings) */}
                                <mesh position={[0, 0.2 * data.scale, 0]}>
                                    <torusGeometry args={[data.scale * 0.11, data.scale * 0.02, 8, 16]} />
                                    <meshStandardMaterial color="#ffffff" />
                                </mesh>
                                <mesh position={[0, -0.2 * data.scale, 0]}>
                                    <torusGeometry args={[data.scale * 0.11, data.scale * 0.02, 8, 16]} />
                                    <meshStandardMaterial color="#ffffff" />
                                </mesh>
                            </group>
                        )}

                    </group>
                </Float>
            ))}
        </group>
    );
};

const TreeScene = ({ treeState }: { treeState: any }) => {
    return (
        <div className="w-full h-full bg-[#050505]">
            <Canvas shadows camera={{ position: [0, 2, 9], fov: 45 }}>
                <fog attach="fog" args={['#050505', 5, 30]} />

                <ambientLight intensity={0.6} />
                <spotLight position={[10, 15, 10]} angle={0.25} penumbra={1} intensity={1.5} castShadow shadow-bias={-0.0001} />
                <pointLight position={[-5, 5, -5]} intensity={0.5} color="#60a5fa" />
                <pointLight position={[5, 3, 5]} intensity={0.3} color="#fbbf24" />

                <Stars radius={100} depth={50} count={3000} factor={4} saturation={0} fade speed={1} />
                <Sparkles count={200} scale={15} size={2} speed={0.5} opacity={0.6} color="#fff" />

                <RoamingItems />
                <Tree treeState={treeState} />

                {/* Shadow Catcher Ground */}
                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2.5, 0]} receiveShadow>
                    <planeGeometry args={[100, 100]} />
                    <shadowMaterial opacity={0.5} />
                </mesh>

                <OrbitControls enablePan={false} maxPolarAngle={Math.PI / 2 - 0.05} minDistance={4} maxDistance={15} autoRotate autoRotateSpeed={0.5} />

                <EffectComposer enableNormalPass={false}>
                    <Bloom luminanceThreshold={0.9} mipmapBlur intensity={1} radius={0.5} />
                </EffectComposer>
            </Canvas>
        </div>
    );
};

export default TreeScene;
