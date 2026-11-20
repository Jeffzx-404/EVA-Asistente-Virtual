import QtQuick

QtObject {
    // Única definición de color y actividad. Los shaders reciben estas paletas interpoladas.
    readonly property var states: ({
        "LISTA":       { primary: "#785bff", secondary: "#328dff", activity: .65 },
        "ESCUCHANDO":  { primary: "#0de6e6", secondary: "#36bfff", activity: 1.1 },
        "PROCESANDO":  { primary: "#ef31df", secondary: "#963dff", activity: 1.5 },
        "HABLANDO":    { primary: "#247aff", secondary: "#9c62ff", activity: 1.2 },
        "ACLARACIÓN":  { primary: "#ffc136", secondary: "#ff811f", activity: .45 },
        "ERROR":       { primary: "#ff2543", secondary: "#ed2474", activity: .9 },
        "STANDBY":     { primary: "#556fc6", secondary: "#397cbc", activity: .22 }
    })
}
