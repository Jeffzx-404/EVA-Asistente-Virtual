import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtQuick3D
import QtQuick3D.Helpers
import EVABrainV53 1.0

Window {
    id: win
    width: 1400
    height: 820
    minimumWidth: 860
    minimumHeight: 640
    visible: true
    color: "#020510"
    title: "EVA · Neural Brain V5.3 · Demostración independiente"
    property bool lowQuality: false
    property bool reducedMotion: false
    property bool gentleMotion: false
    property bool showPanel: false
    property string qualityMode: "ALTA"
    property string qualityReason: "Selección manual"
    readonly property bool slowClock: gentleMotion || currentMode === "STANDBY"
    readonly property real motionScale: gentleMotion ? .35 : 1
    VoiceReactivity {
        id: voice
        objectName: "voiceReactivity"
        suspended: !win.active || win.reducedMotion
    }
    readonly property real speechEnergy: voice.speechLevelSmoothed * win.speakingMotion
    PerformanceMonitor {
        id: monitor
        objectName: "performanceMonitor"
        running: win.active && !win.reducedMotion
        onRecommended: (low, reason) => { win.lowQuality = low; win.qualityReason = reason }
    }
    Component.onCompleted: monitor.attach(win)
    function selectQuality(mode) {
        if (["ALTA","REDUCIDA","AUTOMÁTICA"].indexOf(mode)<0) return
        qualityMode = mode
        if (mode !== "AUTOMÁTICA") lowQuality = mode === "REDUCIDA"
        qualityReason = mode === "AUTOMÁTICA" ? "Observando ventanas de rendimiento" : "Selección manual"
    }
    property bool anatomyView: false
    property bool showControls: true
    property string currentMode: "LISTA"
    property string previousMode: "LISTA"
    property real elapsed: 0
    readonly property real shaderTime: elapsed % 4096
    property real userYaw: 0
    property real cameraDistance: 600
    property bool active: visible && visibility !== Window.Minimized
    StatePalette { id: palette }
    property color accent: palette.states[currentMode].primary
    property color secondary: palette.states[currentMode].secondary
    property vector3d tint: Qt.vector3d(accent.r, accent.g, accent.b)
    property vector3d secondaryTint: Qt.vector3d(secondary.r, secondary.g, secondary.b)
    property real activity: palette.states[currentMode].activity
    // Se mezclan trayectorias completas, no se multiplica el tiempo por velocidad:
    // así no hay saltos de fase al seleccionar otro estado.
    property real listeningMotion: 0
    property real processingMotion: 0
    property real speakingMotion: 0
    property real errorMotion: 0
    property real standbyMotion: 0
    property real waitingMotion: 0
    Behavior on accent { ColorAnimation { duration: 900 } }
    Behavior on secondary { ColorAnimation { duration: 900 } }
    Behavior on activity { NumberAnimation { duration: 1100; easing.type: Easing.InOutSine } }
    Behavior on userYaw { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }
    Behavior on cameraDistance { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }

    function selectMode(mode) {
        const aliases = { IDLE: "LISTA", LISTENING: "ESCUCHANDO", PROCESSING: "PROCESANDO", SPEAKING: "HABLANDO" }
        mode = aliases[mode] || mode
        if (!palette.states[mode]) return
        errorTimer.stop()
        if (mode === "ERROR") {
            if (currentMode !== "ERROR") previousMode = currentMode
            errorTimer.start()
        }
        currentMode = mode
    }
    Timer {
        id: errorTimer
        interval: 3200
        onTriggered: win.currentMode = win.previousMode
    }
    function advance(delta) {
            const dt = Math.min(delta, .08)
            voice.advance(dt, win.currentMode === "HABLANDO")
            win.elapsed += dt * (win.gentleMotion ? .35 : win.currentMode === "STANDBY" ? .22 : 1)
            // Suavizado temporal (~99 % en 0,8 s). Pausa también la mezcla de patrones.
            const blend = 1-Math.exp(-6*dt)
            win.listeningMotion += ((win.currentMode === "ESCUCHANDO" ? 1 : 0)-win.listeningMotion)*blend
            win.processingMotion += ((win.currentMode === "PROCESANDO" ? 1 : 0)-win.processingMotion)*blend
            win.speakingMotion += ((win.currentMode === "HABLANDO" ? 1 : 0)-win.speakingMotion)*blend
            win.errorMotion += ((win.currentMode === "ERROR" ? 1 : 0)-win.errorMotion)*blend
            win.standbyMotion += ((win.currentMode === "STANDBY" ? 1 : 0)-win.standbyMotion)*blend
            win.waitingMotion += ((win.currentMode === "ACLARACIÓN" ? 1 : 0)-win.waitingMotion)*blend
    }
    FrameAnimation {
        id: animationClock
        running: win.active && !win.reducedMotion && !win.slowClock
        onTriggered: win.advance(frameTime)
    }
    Timer {
        id: slowTicker
        interval: 33; repeat: true
        running: win.active && !win.reducedMotion && win.slowClock
        property real previousTime: 0
        onRunningChanged: previousTime = Date.now()
        onTriggered: { const now = Date.now(); win.advance((now-previousTime)/1000); previousTime = now }
    }
    onClosing: { animationClock.running = false; slowTicker.stop(); errorTimer.stop(); monitor.stop(); voice.stop() }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0; color: "#030817" }
            GradientStop { position: .6; color: "#030614" }
            GradientStop { position: 1; color: "#010309" }
        }
    }
    BinaryField {
        id: rain
        anchors.fill: parent
        sceneTime: win.elapsed
        lowQuality: win.lowQuality
        stateTint: win.accent
        opacity: .92*(1-.60*win.standbyMotion)
        // Radio de la silueta de una esfera en perspectiva: incluye margen y fade.
        readonly property real projectedRadius: (view.height*.5/Math.tan(camera.fieldOfView*Math.PI/360))
            *187/Math.sqrt(win.cameraDistance*win.cameraDistance-187*187)
        exclusionCenter: Qt.vector2d(view.x+view.width*.5,view.y+view.height*.5)
        exclusionRadius: Qt.vector2d(projectedRadius+14,projectedRadius+14)
        quietRect: win.showControls ? Qt.vector4d(controls.x-18,controls.y-16,controls.width+36,controls.height+32) : Qt.vector4d(0,0,0,0)
        panelRect: win.showPanel ? Qt.vector4d(demoPanel.x-12,demoPanel.y-12,demoPanel.width+24,demoPanel.height+24) : Qt.vector4d(0,0,0,0)
    }
    View3D {
        id: view
        objectName: "brainViewport"
        anchors.fill: parent
        anchors.topMargin: 58
        anchors.bottomMargin: win.showControls ? controls.height+70 : 40
        anchors.rightMargin: win.showPanel && win.width >= 1250 ? 340 : 0
        renderMode: View3D.Offscreen
        explicitTextureWidth: Math.max(1, Math.round(width * Screen.devicePixelRatio * (win.lowQuality ? .65 : 1)))
        explicitTextureHeight: Math.max(1, Math.round(height * Screen.devicePixelRatio * (win.lowQuality ? .65 : 1)))
        environment: ExtendedSceneEnvironment {
            backgroundMode: SceneEnvironment.Transparent
            antialiasingMode: win.lowQuality ? SceneEnvironment.NoAA : SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
            tonemapMode: SceneEnvironment.TonemapModeFilmic
            glowEnabled: !win.lowQuality && !win.anatomyView
            glowStrength: .85
            glowIntensity: .75
            glowBloom: .05
            glowHDRMinimumValue: .8
            glowHDRScale: 1.3
            glowQualityHigh: false
            glowLevel: 7
        }
        camera: camera
        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, win.cameraDistance)
            fieldOfView: 38
            clipNear: 10
            clipFar: 1600
        }
        Model {
            objectName: "sideCircuits"
            visible: !win.anatomyView
            geometry: NeuralGeometry { kind: "circuits" }
            materials: CustomMaterial {
                objectName: "circuitMaterial"
                shadingMode: CustomMaterial.Unshaded
                property real uTime: win.shaderTime
                property real uSpeed: .14
                property real uProcessing: win.processingMotion
                property real uSpeaking: win.speakingMotion
                property real uStandby: win.standbyMotion
                // Paleta ya interpolada del cerebro; sin una segunda transición.
                property real uEnergy: (1.8+.45*win.processingMotion+.20*win.listeningMotion)
                    * (1+.15*win.speechEnergy)
                property real uBase: .14
                property real uOpacity: .56*(1-.35*win.standbyMotion)
                property vector3d uTint: win.tint
                property vector3d uSecondary: win.secondaryTint
                property real uListening: win.listeningMotion
                sourceBlend: CustomMaterial.SrcAlpha
                destinationBlend: CustomMaterial.OneMinusSrcAlpha
                vertexShader: "shaders/network.vert"
                fragmentShader: "shaders/circuits.frag"
            }
        }
        Node {
            id: brainRig
            objectName: "brainRig"
            // Perfil dominante, ligera vista del otro hemisferio. ±7 grados, sin saltos.
            eulerRotation: Qt.vector3d(-5 + Math.sin(win.elapsed*.13)*2,
                                      -15 + win.userYaw + Math.sin(win.elapsed*.11)*7, -5)
            Model {
                objectName: "cortexModel"
                geometry: BrainSurface { lowQuality: win.lowQuality }
                materials: CustomMaterial {
                    objectName: "cortexMaterial"
                    shadingMode: CustomMaterial.Unshaded
                    cullMode: Material.BackFaceCulling
                    depthDrawMode: win.anatomyView ? Material.AlwaysDepthDraw : Material.OpaqueOnlyDepthDraw
                    sourceBlend: CustomMaterial.SrcAlpha
                    destinationBlend: win.anatomyView ? CustomMaterial.OneMinusSrcAlpha : CustomMaterial.One
                    property real uTime: win.shaderTime
                    property vector3d uTint: win.tint
                    property vector3d uSecondary: win.secondaryTint
                    property real uAnatomy: win.anatomyView ? 1 : 0
                    vertexShader: "shaders/cortex.vert"
                    fragmentShader: "shaders/cortex.frag"
                }
            }
            Model {
                visible: !win.anatomyView
                geometry: NeuralGeometry { kind: "filaments" }
                materials: CustomMaterial {
                    shadingMode: CustomMaterial.Unshaded
                    property real uTime: win.shaderTime
                    property real uSpeed: .18
                    property real uProcessing: win.processingMotion
                    property real uSpeaking: win.speakingMotion
                    property real uStandby: win.standbyMotion
                    property real uEnergy: 3.7 * win.activity * (1 + .20*win.speechEnergy)
                    property real uBase: .30
                    property real uOpacity: .8
                    property vector3d uTint: win.tint
                    property vector3d uSecondary: win.secondaryTint
                    sourceBlend: CustomMaterial.SrcAlpha
                    destinationBlend: CustomMaterial.One
                    vertexShader: "shaders/network.vert"
                    fragmentShader: "shaders/network.frag"
                }
            }
            Model {
                objectName: "neuralNodes"
                visible: !win.anatomyView
                geometry: NeuralGeometry { kind: "particles"; lowQuality: win.lowQuality }
                materials: CustomMaterial {
                    objectName: "neuralMotionMaterial"
                    shadingMode: CustomMaterial.Unshaded
                    cullMode: Material.NoCulling
                    property real uTime: win.shaderTime
                    property real uEnergy: 3.5 * win.activity
                    property real uOpacity: 1
                    property vector3d uTint: win.tint
                    property real uListening: win.listeningMotion
                    property real uProcessing: win.processingMotion
                    property real uSpeaking: win.speakingMotion
                    property real uError: win.errorMotion
                    property real uStandby: win.standbyMotion
                    property real uWaiting: win.waitingMotion
                    property real uMotionScale: win.motionScale
                    property real uSpeechLevel: voice.speechLevelSmoothed
                    property real uSpeechMix: voice.reactivityBlend
                    property real uSpeechJumpStrength: 3.0 * voice.speechJumpStrength * (win.gentleMotion ? .35 : 1)
                    property real uSpeechWaveBoost: win.lowQuality ? .20 : .30
                    property real uSpeechGlowBoost: win.gentleMotion ? .18 : .25
                    sourceBlend: CustomMaterial.SrcAlpha
                    destinationBlend: CustomMaterial.One
                    vertexShader: "shaders/neural_motion.vert"
                    fragmentShader: "shaders/particle.frag"
                }
            }
            Model {
                visible: !win.anatomyView
                scale: Qt.vector3d(.77,.77,.77)
                geometry: NeuralGeometry { kind: "innerFilaments" }
                materials: CustomMaterial {
                    shadingMode: CustomMaterial.Unshaded
                    property real uTime: win.shaderTime
                    property real uSpeed: .11
                    property real uProcessing: win.processingMotion
                    property real uSpeaking: win.speakingMotion
                    property real uStandby: win.standbyMotion
                    property real uEnergy: 1.2*win.activity*(1 + .15*win.speechEnergy)
                    property real uBase: .10
                    property real uOpacity: .25
                    property vector3d uTint: win.secondaryTint
                    property vector3d uSecondary: win.tint
                    sourceBlend: CustomMaterial.SrcAlpha
                    destinationBlend: CustomMaterial.One
                    vertexShader: "shaders/network.vert"
                    fragmentShader: "shaders/network.frag"
                }
            }
            Model {
                visible: !win.anatomyView
                source: "#Rectangle"
                position: Qt.vector3d(0,12,-18)
                scale: Qt.vector3d(1.25,1.25,1)
                materials: CustomMaterial {
                    shadingMode: CustomMaterial.Unshaded
                    property real uTime: win.shaderTime
                    property vector3d uTint: win.tint
                    sourceBlend: CustomMaterial.SrcAlpha
                    destinationBlend: CustomMaterial.One
                    vertexShader: "shaders/network.vert"
                    fragmentShader: "shaders/core.frag"
                    property real uSpeechLevel: win.speechEnergy
                }
            }
        }
        Model {
            objectName: "cosmicModel"
            visible: !win.anatomyView
            geometry: NeuralGeometry { kind: "cosmic"; lowQuality: win.lowQuality }
            materials: CustomMaterial {
                shadingMode: CustomMaterial.Unshaded
                cullMode: Material.NoCulling
                property real uTime: win.shaderTime
                property vector2d uParallax: Qt.vector2d(win.userYaw*.20,0)
                property vector3d uTint: win.tint
                sourceBlend: CustomMaterial.SrcAlpha
                destinationBlend: CustomMaterial.One
                vertexShader: "shaders/cosmic.vert"
                fragmentShader: "shaders/cosmic.frag"
            }
        }
        Model {
            visible: !win.anatomyView
            geometry: NeuralGeometry { kind: "shellParticles"; lowQuality: win.lowQuality }
            materials: CustomMaterial {
                shadingMode: CustomMaterial.Unshaded
                cullMode: Material.NoCulling
                property real uTime: win.shaderTime
                property real uEnergy: 1.8
                property real uOpacity: .32
                property vector3d uTint: win.secondaryTint
                sourceBlend: CustomMaterial.SrcAlpha
                destinationBlend: CustomMaterial.One
                vertexShader: "shaders/particle.vert"
                fragmentShader: "shaders/particle.frag"
            }
        }
        Model {
            visible: !win.anatomyView
            source: "#Sphere"
            scale: Qt.vector3d(3.74, 3.74, 3.74)
            materials: CustomMaterial {
                shadingMode: CustomMaterial.Unshaded
                cullMode: Material.BackFaceCulling
                sourceBlend: CustomMaterial.SrcAlpha
                destinationBlend: CustomMaterial.OneMinusSrcAlpha
                property real uTime: win.shaderTime
                vertexShader: "shaders/cortex.vert"
                fragmentShader: "shaders/globe.frag"
                property vector3d uTint: win.tint
            }
        }
        Model {
            visible: !win.anatomyView
            geometry: NeuralGeometry { kind: "globe" }
            materials: CustomMaterial {
                shadingMode: CustomMaterial.Unshaded
                property real uTime: win.shaderTime
                property real uSpeed: .035
                property real uProcessing: win.processingMotion
                property real uSpeaking: win.speakingMotion
                property real uStandby: win.standbyMotion
                property real uEnergy: 1.5
                property real uBase: .14
                property real uOpacity: .18
                property vector3d uTint: win.tint
                property vector3d uSecondary: win.secondaryTint
                sourceBlend: CustomMaterial.SrcAlpha
                destinationBlend: CustomMaterial.OneMinusSrcAlpha
                vertexShader: "shaders/network.vert"
                fragmentShader: "shaders/network.frag"
            }
        }
    }

    MouseArea {
        anchors.fill: view
        property real lastX: 0
        onPressed: mouse => lastX = mouse.x
        onPositionChanged: mouse => {
            if (pressed) {
                win.userYaw = Math.max(-20, Math.min(20, win.userYaw + (mouse.x-lastX)*.15))
                lastX = mouse.x
            }
        }
        onWheel: wheel => win.cameraDistance = Math.max(560,Math.min(800,win.cameraDistance-wheel.angleDelta.y*.14))
        onDoubleClicked: { win.userYaw = 0; win.cameraDistance = 600 }
    }
    Row {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: 30
        spacing: 16
        Text { text: "E V A"; color: "#e1e4ff"; font.pixelSize: 22; font.letterSpacing: 5 }
        Rectangle { width: 1; height: 25; color: "#303b60" }
        Column {
            spacing: 3
            Text { text: "NEURAL BRAIN"; color: "#8b96c1"; font.pixelSize: 10; font.letterSpacing: 3 }
            Text { text: "V5.3 / PRESENCIA DIGITAL"; color: "#465578"; font.pixelSize: 8; font.letterSpacing: 1.4 }
        }
    }
    Column {
        anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 32
        spacing: 4
        Text { text: win.currentMode + "  ·  DEMO"; color: win.accent; font.pixelSize: 12; anchors.right: parent.right }
        Text { text: (win.qualityMode === "AUTOMÁTICA" ? "AUTO / " : "CALIDAD ") + (win.lowQuality ? "REDUCIDA" : "ALTA")
            + (win.reducedMotion ? "  ·  PAUSA" : monitor.fps > 0 ? "  ·  " + monitor.fps.toFixed(1) + " FPS" : "  ·  MIDIENDO")
            color: "#91a6c8"; font.pixelSize: 10; anchors.right: parent.right }
    }
    Column {
        id: controls
        visible: win.showControls
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 60
        spacing: 12
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 9
            Rectangle { width: 5; height: 5; radius: 3; color: win.accent; anchors.verticalCenter: parent.verticalCenter }
            Text { text: win.currentMode; color: win.accent; font.pixelSize: 11; font.letterSpacing: 3 }
            Text { text: "  /  SEÑAL SIMULADA"; color: "#58688e"; font.pixelSize: 9; anchors.verticalCenter: parent.verticalCenter }
        }
        Flow {
            width: Math.min(win.width-40, 850)
            spacing: 8
            Repeater {
                model: ["LISTA","ESCUCHANDO","PROCESANDO","HABLANDO","ACLARACIÓN","ERROR","STANDBY"]
                delegate: ControlButton {
                    required property string modelData
                    objectName: "state-" + modelData
                    text: modelData
                    selected: win.currentMode === modelData
                    accent: win.accent
                    onClicked: win.selectMode(modelData)
                }
            }
        }
        Flow {
            width: Math.min(win.width-40,850)
            spacing: 8
            DemoComboBox {
                objectName: "qualitySelector"
                width: 170; height: 40
                model: ["ALTA","REDUCIDA","AUTOMÁTICA"]
                currentIndex: model.indexOf(win.qualityMode)
                onActivated: win.selectQuality(currentText)
                Accessible.name: "Calidad gráfica"
            }
            ControlButton { objectName: "gentleButton"; text: "MOVIMIENTO SUAVE"; selected: win.gentleMotion; onClicked: win.gentleMotion = !win.gentleMotion }
            ControlButton { objectName: "pauseButton"; text: win.reducedMotion ? "REANUDAR" : "PAUSAR"; selected: win.reducedMotion; onClicked: win.reducedMotion = !win.reducedMotion }
            ControlButton { objectName: "panelButton"; text: win.showPanel ? "OCULTAR PANEL" : "EXPLORAR EVA"; selected: win.showPanel; onClicked: win.showPanel = !win.showPanel }
        }
        Flow {
            width: Math.min(win.width-40,850)
            spacing: 8
            ControlButton {
                objectName: "voiceToggle"
                text: voice.enabled ? "REACCIÓN DE VOZ: SÍ" : "REACCIÓN DE VOZ: NO"
                selected: voice.enabled
                onClicked: voice.enabled = !voice.enabled
            }
            DemoComboBox {
                objectName: "voiceIntensity"
                width: 190; height: 40
                model: ["VOZ SIMULADA · SUAVE", "VOZ SIMULADA · MEDIA", "VOZ SIMULADA · INTENSA"]
                currentIndex: voice.demoIntensity < .5 ? 0 : voice.demoIntensity < .85 ? 1 : 2
                onActivated: voice.demoIntensity = [.35,.65,1.0][currentIndex]
                Accessible.name: "Intensidad de voz simulada"
            }
            Row {
                height: 40; spacing: 8
                Rectangle {
                    width: 72; height: 5; radius: 2; color: "#1d2941"
                    anchors.verticalCenter: parent.verticalCenter
                    Rectangle { width: parent.width*win.speechEnergy; height: parent.height; radius: 2; color: win.accent }
                }
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: voice.source === "DEMO" ? "SIMULACIÓN · SOLO HABLANDO" : "NIVEL EXTERNO"
                    color: "#91a6c8"; font.pixelSize: 10
                }
            }
        }
    }
    Row {
        anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 18; spacing: 6
        ControlButton { text: win.anatomyView ? "HOLOGRAMA" : "ANATOMÍA"; onClicked: win.anatomyView = !win.anatomyView }
        ControlButton { objectName: "cinemaButton"; text: win.showControls ? "CINE" : "CONTROLES"; onClicked: { win.showControls = !win.showControls; win.showPanel = false } }
    }
    DemoPanel {
        id: demoPanel
        objectName: "demoPanel"
        visible: win.showPanel
        anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
        anchors.rightMargin: 16; anchors.topMargin: 100; anchors.bottomMargin: 110
        width: Math.min(330,win.width-32)
        accent: win.accent
        onCloseRequested: win.showPanel = false
        onModeRequested: mode => win.selectMode(mode)
    }
    Text {
        anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.margins: 25
        text: "MODELO: DGALLICHAN · CC BY 4.0"
        color: "#485675"; font.pixelSize: 8; font.letterSpacing: 1
    }
    Shortcut { sequence: "Escape"; onActivated: { win.showControls = true; win.showPanel = false } }
    Shortcut { sequence: "Space"; enabled: !win.showPanel; onActivated: win.reducedMotion = !win.reducedMotion }
}
