import QtQuick

ShaderEffect {
    id: rain
    objectName: "matrixBackground"
    property real sceneTime: 0
    property bool lowQuality: false
    property color stateTint: "#785bff"
    property vector2d exclusionCenter: Qt.vector2d(width*.5,height*.5)
    property vector2d exclusionRadius: Qt.vector2d(200,200)
    property vector4d quietRect: Qt.vector4d(0,0,0,0)
    property vector4d panelRect: Qt.vector4d(0,0,0,0)
    property real maskEnabled: 1
    readonly property vector2d resolution: Qt.vector2d(width,height)
    readonly property real lowDetail: lowQuality ? 1 : 0
    property var glyphAtlas: Image {
        source: "../assets/binary_glyphs.svg"
        sourceSize: Qt.size(256,160)
        smooth: true
        visible: false
    }
    blending: true
    fragmentShader: "shaders/matrix.frag.qsb"
}
