import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick

// Pixel Autumn Leaves: animated wallpaper layer (Bottom, above the static
// wallpaper, below every window). It only exists while the active Omarchy
// theme is "Pixel Autumn"; with any other theme no window is created and the
// plugin costs nothing.
Scope {
  id: root

  readonly property string home: Quickshell.env("HOME")
  readonly property string sceneUrl: Qt.resolvedUrl("scene.png")
  readonly property string treesPath: Qt.resolvedUrl("trees.json").toString().replace("file://", "")

  property string themeName: ""
  readonly property bool active: themeName.toLowerCase().replace(/[^a-z0-9]/g, "") === "pixelautumn"
  property var info: ({ scene: [480, 270], groundY: 222, groundMax: 262, trees: [] })

  // The current theme name is written by `omarchy theme set`.
  FileView {
    id: themeFile
    path: root.home + "/.local/state/omarchy/current/theme.name"
    watchChanges: true
    onFileChanged: reload()
    onLoaded: root.themeName = String(text()).trim()
  }

  // Safety net in case a file watch event is missed (replaced file, etc.).
  Timer {
    interval: 5000
    repeat: true
    running: true
    onTriggered: themeFile.reload()
  }

  FileView {
    id: treesFile
    path: root.treesPath
    blockLoading: true
    onLoaded: {
      try { root.info = JSON.parse(String(text())) } catch (e) { console.warn("pixel-autumn-leaves: invalid trees.json", e) }
    }
  }

  Variants {
    model: root.active ? Quickshell.screens : []

    PanelWindow {
      id: panel
      required property var modelData
      screen: modelData
      anchors { top: true; bottom: true; left: true; right: true }
      color: "black"
      mask: Region {}

      WlrLayershell.namespace: "pixel-autumn-leaves"
      WlrLayershell.layer: WlrLayer.Bottom
      WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
      exclusionMode: ExclusionMode.Ignore

      Item {
        id: world
        width: root.info.scene[0]
        height: root.info.scene[1]
        scale: Math.max(panel.width / width, panel.height / height)
        transformOrigin: Item.TopLeft

        Image {
          anchors.fill: parent
          source: root.sceneUrl
          smooth: false
          mipmap: false
          cache: true
        }

        Repeater {
          id: leaves
          model: 25

          Rectangle {
            id: leaf
            antialiasing: false
            smooth: false
            width: 3
            height: 2
            visible: false
            color: "#f5c542"

            // 0 waiting, 1 falling, 2 resting, 3 fading
            property int state: 0
            property real wait: Math.random() * 10
            property real lx: 0
            property real ly: 0
            property real targetY: 0
            property real speed: 20
            property real amp: 4
            property real freq: 1
            property real phase: 0
            property real age: 0
            property real rotT: 0
            property bool flip: false
            property real restT: 0

            function spawn() {
              var trees = root.info.trees
              if (!trees || trees.length === 0) { wait = 2; state = 0; return }
              var total = 0, i
              for (i = 0; i < trees.length; i++) total += trees[i].rx * trees[i].ry
              var pick = Math.random() * total
              var t = trees[0]
              for (i = 0; i < trees.length; i++) {
                pick -= trees[i].rx * trees[i].ry
                if (pick <= 0) { t = trees[i]; break }
              }
              // Spawn on a real foliage pixel of the chosen tree.
              if (t.pts && t.pts.length > 0) {
                var p = t.pts[Math.floor(Math.random() * t.pts.length)]
                lx = p[0]
                ly = p[1]
              } else {
                lx = t.x
                ly = t.y
              }
              var top = t.base - 4
              var span = Math.min(root.info.groundMax - top, 34)
              targetY = top + Math.random() * span
              if (targetY < ly + 4) targetY = ly + 4 + Math.random() * 20
              speed = 15 + Math.random() * 15
              amp = 3 + Math.random() * 6
              freq = 0.8 + Math.random() * 1.2
              phase = Math.random() * 6.28
              age = 0
              rotT = 0
              flip = Math.random() < 0.5
              color = t.pal ? t.pal[Math.floor(Math.random() * t.pal.length)] : "#f5c542"
              opacity = 1
              state = 1
              place(lx, ly)
              visible = true
            }

            function place(px, py) {
              x = Math.round(px)
              y = Math.round(py)
              width = flip ? 2 : 3
              height = flip ? 3 : 2
            }

            function step(dt) {
              if (state === 0) {
                wait -= dt
                if (wait <= 0) spawn()
              } else if (state === 1) {
                age += dt
                ly += speed * dt
                rotT += dt
                if (rotT > 0.45) { rotT = 0; flip = !flip }
                if (ly >= targetY) {
                  ly = targetY
                  state = 2
                  restT = 3 + Math.random() * 4
                  place(lx + Math.sin(phase + age * freq) * amp, ly)
                  return
                }
                place(lx + Math.sin(phase + age * freq) * amp, ly)
              } else if (state === 2) {
                restT -= dt
                if (restT <= 0) { state = 3; restT = 1.6 }
              } else if (state === 3) {
                restT -= dt
                // opacity in 4 steps, pixel art style
                opacity = Math.max(0, Math.ceil(restT / 1.6 * 4) / 4)
                if (restT <= 0) {
                  visible = false
                  state = 0
                  wait = 0.5 + Math.random() * 6
                }
              }
            }
          }
        }
      }

      // 20 fps is plenty for 1-3 px leaves and keeps CPU low.
      Timer {
        interval: 50
        repeat: true
        running: true
        property double last: Date.now()
        onTriggered: {
          var now = Date.now()
          var dt = Math.min(0.2, (now - last) / 1000)
          last = now
          for (var i = 0; i < leaves.count; i++) leaves.itemAt(i).step(dt)
        }
      }
    }
  }
}
