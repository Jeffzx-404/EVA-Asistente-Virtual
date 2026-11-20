import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: panel
    property color accent: "#8d83d8"
    property string section: "Conversación"
    onSectionChanged: reply.text = ""
    signal closeRequested()
    signal modeRequested(string mode)
    color: "#f2081020"
    border.color: "#364864"
    radius: 12
    clip: true
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 18; spacing: 12
        RowLayout {
            Layout.fillWidth: true
            Label { text: "ESPACIO EVA"; color: "#e4ebff"; font.pixelSize: 17; Layout.fillWidth: true }
            ControlButton { objectName: "closePanel"; text: "CERRAR"; onClicked: panel.closeRequested() }
        }
        Label { text: "Demostración · sin servicios conectados"; color: "#8dacca"; wrapMode: Text.Wrap; Layout.fillWidth: true }
        DemoComboBox {
            objectName: "demoNavigation"
            Layout.fillWidth: true
            model: ["Conversación","Recordatorios","Alarmas","Configuración","Servicios"]
            currentIndex: model.indexOf(panel.section)
            onActivated: panel.section = currentText
            Accessible.name: "Sección de demostración"
        }
        ScrollView {
            id: scroll
            Layout.fillWidth: true; Layout.fillHeight: true
            contentWidth: availableWidth
            clip: true
            ColumnLayout {
                width: scroll.availableWidth
                spacing: 14
                Label { text: panel.section; color: panel.accent; font.pixelSize: 20 }
                Label {
                    Layout.fillWidth: true; wrapMode: Text.Wrap; color: "#c5d3ea"
                    text: panel.section === "Conversación" ? "EVA\nEstoy lista. Puedes probar el texto o el micrófono simulado."
                        : panel.section === "Recordatorios" ? "Ejemplo de recordatorio\nRevisar los apuntes · hoy, 18:00\n\nEste ejemplo no se guarda ni genera avisos."
                        : panel.section === "Alarmas" ? "Ejemplo de alarma\n07:30 · desactivada\n\nNo se programan alarmas del sistema."
                        : panel.section === "Configuración" ? "Los controles de calidad, movimiento suave y pausa están bajo el cerebro. Los cambios solo afectan a esta demo."
                        : "Voz · desconectada\nInteligencia local · desconectada\nSpotify · desconectado\nGemini · desconectado"
                }
                Label { id: reply; Layout.fillWidth: true; wrapMode: Text.Wrap; color: "#d7e4ff"; text: "" }
            }
        }
        TextField {
            id: input
            objectName: "demoInput"
            Layout.fillWidth: true
            implicitHeight: 40
            visible: panel.section === "Conversación"
            placeholderText: "Escribe una prueba…"
            maximumLength: 300
            color: "#dbe6f9"
            placeholderTextColor: "#8a9bb5"
            background: Rectangle { radius: 5; color: "#081225"; border.color: input.activeFocus ? panel.accent : "#42526d" }
            Accessible.name: "Texto de demostración"
            onAccepted: send.clicked()
        }
        RowLayout {
            visible: panel.section === "Conversación"
            ControlButton { id: send; objectName: "demoSend"; text: "ENVIAR"; onClicked: {
                if (!input.text.trim()) return
                reply.text = "Respuesta de demostración. No se ha enviado información a ningún servicio."
                input.clear(); panel.modeRequested("HABLANDO")
            } }
            ControlButton { objectName: "demoMic"; text: "MICRÓFONO DEMO"; onClicked: {
                reply.text = "Escucha simulada: no se está capturando audio."
                panel.modeRequested("ESCUCHANDO")
            } }
        }
    }
}
