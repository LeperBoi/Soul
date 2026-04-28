import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from matplotlib.widgets import RadioButtons, Button
import os
from tkinter import Tk, filedialog
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================
LINE_THICKNESS = 0.12
SYMBOL_SIZE = 0.22

EMOTIONS = [
    "Joy", "Trust", "Fear", "Surprise",
    "Sorrow", "Disgust", "Anger", "Anticipation"
]

SHADOW_EMOTIONS = [
    "Narcissism", "Confirmation Bias", "Psychopathy", "Repetition Compulsion",
    "Masochism", "Prejudice", "Sadism", "Machiavellianism"
]

# Regular labels (control central star)
REGULAR_LABELS = ["N/A", "Expressed", "Suppressed", "Repressed"]
# Spirit labels (control spirit star triangles)
SPIRIT_LABELS = ["N/A", "Ego", "Shadow"]

# =====================================================
# GEOMETRY & DRAWING FUNCTIONS
# =====================================================
def rotate(points, angle):
    rot = np.array([[np.cos(angle), -np.sin(angle)],
                    [np.sin(angle), np.cos(angle)]])
    return np.dot(points, rot.T)

def transform(points, angle, scale, x, y):
    pts = rotate(points, angle)
    pts *= scale
    pts[:, 0] += x
    pts[:, 1] += y
    return pts

def draw_thick_line(ax, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    length = np.sqrt(dx*dx + dy*dy)
    if length == 0:
        return
    dx /= length
    dy /= length
    px, py = -dy, dx
    half = LINE_THICKNESS / 2
    corners = [
        [x1 + px*half, y1 + py*half],
        [x1 - px*half, y1 - py*half],
        [x2 - px*half, y2 - py*half],
        [x2 + px*half, y2 + py*half]
    ]
    ax.add_patch(Polygon(corners, closed=True, color="black"))

def draw_extended_thick_line(ax, x1, y1, x2, y2, extend_start=True, extend_end=True):
    dx = x2 - x1
    dy = y2 - y1
    length = np.sqrt(dx*dx + dy*dy)
    if length == 0:
        return
    dx /= length
    dy /= length
    extension = LINE_THICKNESS / 2

    x1_ext = x1 - dx * extension if extend_start else x1
    y1_ext = y1 - dy * extension if extend_start else y1
    x2_ext = x2 + dx * extension if extend_end else x2
    y2_ext = y2 + dy * extension if extend_end else y2

    px, py = -dy, dx
    half = LINE_THICKNESS / 2
    corners = [
        [x1_ext + px*half, y1_ext + py*half],
        [x1_ext - px*half, y1_ext - py*half],
        [x2_ext - px*half, y2_ext - py*half],
        [x2_ext + px*half, y2_ext + py*half]
    ]
    ax.add_patch(Polygon(corners, closed=True, color="black"))

def draw_symbol(ax, x, y, dx, dy, state, empathized):
    angle = np.arctan2(dy, dx)
    size = SYMBOL_SIZE

    if state == 1:  # EXPRESSED
        arrow = np.array([[1.0, 0.0], [-0.7, 0.6], [-0.7, -0.6]])
        pts = transform(arrow, angle, size, x, y)
        ax.add_patch(Polygon(pts, closed=True, color="black"))
    elif state == 2:  # SUPPRESSED
        arrow = np.array([[1.0, 0.0], [-0.7, 0.6], [-0.7, -0.6]])
        pts = transform(arrow, angle, size, x, y)
        ax.add_patch(Polygon(pts, closed=True, color="black"))
        diode = np.array([[0.8, 0.7], [0.8, -0.7]])
        line = transform(diode, angle, size, x, y)
        draw_thick_line(ax, line[0][0], line[0][1], line[1][0], line[1][1])
    elif state == 3:  # REPRESSED
        spacing = 1.0
        for offset in [-spacing/2, spacing/2]:
            bars = np.array([[offset, 0.9], [offset, -0.9]])
            bar = transform(bars, angle, size, x, y)
            draw_thick_line(ax, bar[0][0], bar[0][1], bar[1][0], bar[1][1])
        horizontal = np.array([[-spacing/2, 0], [spacing/2, 0]])
        h_line = transform(horizontal, angle, size, x, y)
        draw_thick_line(ax, h_line[0][0], h_line[0][1], h_line[1][0], h_line[1][1])

    if empathized:
        ax.add_patch(Circle((x, y), SYMBOL_SIZE*1.25, fill=False, linewidth=6, color='black'))

def get_spirit_triangles(scale=1.5):
    sqrt2 = np.sqrt(2)
    rt = scale * (sqrt2 - 1)
    
    triangles = [
        [(0, scale*sqrt2), (-rt, scale), (rt, scale)],
        [(scale, scale), (scale, rt), (rt, scale)],
        [(scale*sqrt2, 0), (scale, rt), (scale, -rt)],
        [(scale, -scale), (scale, -rt), (rt, -scale)],
        [(0, -scale*sqrt2), (-rt, -scale), (rt, -scale)],
        [(-scale, -scale), (-scale, -rt), (-rt, -scale)],
        [(-scale*sqrt2, 0), (-scale, -rt), (-scale, rt)],
        [(-scale, scale), (-scale, rt), (-rt, scale)]
    ]
    return triangles

def draw_spirit_triangle(ax, triangle, state, is_diagonal=False):
    if state == 0:
        return
    elif state == 2:
        poly = Polygon(triangle, closed=True, color='black', alpha=1.0)
        ax.add_patch(poly)
    elif state == 1:
        tri_array = np.array(triangle)
        
        if is_diagonal:
            centroid = np.mean(tri_array, axis=0)
            
            def line_intersection(p1, p2, slope, intercept):
                x1, y1 = p1
                x2, y2 = p2
                if x1 == x2:
                    x_inter = x1
                    y_inter = slope * x_inter + intercept
                    if min(y1, y2) <= y_inter <= max(y1, y2):
                        return (x_inter, y_inter)
                    return None
                
                m_seg = (y2 - y1) / (x2 - x1)
                b_seg = y1 - m_seg * x1
                
                if m_seg == slope:
                    return None
                
                x_inter = (intercept - b_seg) / (m_seg - slope)
                y_inter = slope * x_inter + intercept
                
                if min(x1, x2) <= x_inter <= max(x1, x2) and min(y1, y2) <= y_inter <= max(y1, y2):
                    return (x_inter, y_inter)
                return None
            
            intercept1 = centroid[1] - centroid[0]
            points1 = []
            for i in range(3):
                p1 = tri_array[i]
                p2 = tri_array[(i+1)%3]
                inter = line_intersection(p1, p2, 1, intercept1)
                if inter is not None:
                    points1.append(inter)
            
            intercept2 = centroid[1] + centroid[0]
            points2 = []
            for i in range(3):
                p1 = tri_array[i]
                p2 = tri_array[(i+1)%3]
                inter = line_intersection(p1, p2, -1, intercept2)
                if inter is not None:
                    points2.append(inter)
            
            if len(points1) >= 2:
                draw_thick_line(ax, points1[0][0], points1[0][1], points1[1][0], points1[1][1])
            if len(points2) >= 2:
                draw_thick_line(ax, points2[0][0], points2[0][1], points2[1][0], points2[1][1])
        else:
            centroid = np.mean(tri_array, axis=0)
            
            horizontal_line = []
            for i in range(3):
                x1, y1 = tri_array[i]
                x2, y2 = tri_array[(i+1)%3]
                if (y1 - centroid[1]) * (y2 - centroid[1]) <= 0 and y1 != y2:
                    t = (centroid[1] - y1) / (y2 - y1)
                    x_intersect = x1 + t * (x2 - x1)
                    horizontal_line.append(x_intersect)
            
            if len(horizontal_line) >= 2:
                draw_thick_line(ax, min(horizontal_line), centroid[1],
                               max(horizontal_line), centroid[1])
            
            vertical_line = []
            for i in range(3):
                x1, y1 = tri_array[i]
                x2, y2 = tri_array[(i+1)%3]
                if (x1 - centroid[0]) * (x2 - centroid[0]) <= 0 and x1 != x2:
                    t = (centroid[0] - x1) / (x2 - x1)
                    y_intersect = y1 + t * (y2 - y1)
                    vertical_line.append(y_intersect)
            
            if len(vertical_line) >= 2:
                draw_thick_line(ax, centroid[0], min(vertical_line),
                               centroid[0], max(vertical_line))

def draw_quadrant_line(ax, quadrant, style):
    leg_center = 0.5
    leg_outer = 0.56

    if quadrant == 0:
        if style == 1:
            draw_thick_line(ax, leg_center, 0, 0, leg_center)
        elif style == 2:
            pts = np.array([[0,0], [leg_outer, 0], [0, leg_outer]])
            ax.add_patch(Polygon(pts, closed=True, color="black"))
    elif quadrant == 1:
        if style == 1:
            draw_thick_line(ax, -leg_center, 0, 0, leg_center)
        elif style == 2:
            pts = np.array([[0,0], [-leg_outer, 0], [0, leg_outer]])
            ax.add_patch(Polygon(pts, closed=True, color="black"))
    elif quadrant == 2:
        if style == 1:
            draw_thick_line(ax, -leg_center, 0, 0, -leg_center)
        elif style == 2:
            pts = np.array([[0,0], [-leg_outer, 0], [0, -leg_outer]])
            ax.add_patch(Polygon(pts, closed=True, color="black"))
    elif quadrant == 3:
        if style == 1:
            draw_thick_line(ax, leg_center, 0, 0, -leg_center)
        elif style == 2:
            pts = np.array([[0,0], [leg_outer, 0], [0, -leg_outer]])
            ax.add_patch(Polygon(pts, closed=True, color="black"))

def draw_star(ax, states, empathy, quadrants=None, spirit=False, spirit_triangle_states=None, config_num=None):
    ax.clear()
    
    if spirit_triangle_states is None:
        spirit_triangle_states = [0] * 8

    radius = 1.0
    angles = np.linspace(np.pi/2, np.pi/2 - 2*np.pi, 8, endpoint=False)
    x = radius * np.cos(angles)
    y = radius * np.sin(angles)

    for i in range(8):
        j = (i + 4) % 8
        draw_thick_line(ax, x[i], y[i], x[j], y[j])

    for i in range(8):
        dx = x[i]
        dy = y[i]
        norm = np.sqrt(dx*dx + dy*dy)
        if norm > 0:
            dx /= norm
            dy /= norm
        draw_symbol(ax, x[i], y[i], dx, dy, states[i], empathy[i])

    if quadrants:
        for q, style in quadrants.items():
            if style > 0 and q < 4:
                draw_quadrant_line(ax, q, style)
            elif q == 4 and style == 1:
                ax.add_patch(Circle((0, 0), 0.6, fill=False, linewidth=6, color='black'))

    if spirit:
        spirit_scale = 1.5
        sqrt2 = np.sqrt(2)

        square1 = [(-spirit_scale, -spirit_scale), (spirit_scale, -spirit_scale),
                   (spirit_scale, spirit_scale), (-spirit_scale, spirit_scale)]
        for i in range(4):
            p1 = square1[i]
            p2 = square1[(i+1)%4]
            draw_extended_thick_line(ax, p1[0], p1[1], p2[0], p2[1], True, True)

        square2 = [(spirit_scale*sqrt2, 0), (0, spirit_scale*sqrt2),
                   (-spirit_scale*sqrt2, 0), (0, -spirit_scale*sqrt2)]
        for i in range(4):
            p1 = square2[i]
            p2 = square2[(i+1)%4]
            draw_extended_thick_line(ax, p1[0], p1[1], p2[0], p2[1], True, True)

        triangles = get_spirit_triangles(spirit_scale)
        for i, triangle in enumerate(triangles):
            if spirit_triangle_states[i] > 0:
                is_diagonal = (i % 2 == 1)
                draw_spirit_triangle(ax, triangle, spirit_triangle_states[i], is_diagonal)

    # Add sequence number in bottom left corner if provided
    if config_num is not None:
        ax.text(-1.8, -1.6, f"#{config_num}", 
               ha='left', va='bottom', 
               fontsize=12, fontweight='bold', color='black')

    ax.plot(0, 0, 'o', color='black', markersize=10)
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-2.2, 2.2)
    ax.set_aspect("equal")
    ax.axis("off")

# =====================================================
# FILE SAVE
# =====================================================
def ask_save_filename():
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"Soul_State_{timestamp}.png"

    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        initialfile=default_filename,
        title="Save Soul State As"
    )
    root.destroy()
    return file_path

# =====================================================
# DIAGRAM EDITOR
# =====================================================
class DiagramEditor:
    def __init__(self):
        self.states = [0] * 8
        self.empathy = [False] * 8
        self.quadrants = {i: 0 for i in range(5)}
        self.spirit = False
        self.spirit_triangle_states = [0] * 8
        self.spirit_empathy = [False] * 8

        self.saved_configs = []
        self.radio_controls = []
        self.empathy_controls = []
        self.quadrant_controls = []
        self.radio_axes = []

        plt.rcParams['toolbar'] = 'None'
        self.fig = plt.figure(figsize=(14, 9))
        self.fig.canvas.manager.set_window_title("Soul")

        self.ax = plt.axes([0.3, 0.1, 0.4, 0.8])

        # RIGHT SIDE: Emotions + Empathy buttons
        for i, emotion in enumerate(EMOTIONS):
            y = 0.88 - i * 0.1

            rax = plt.axes([0.72, y, 0.22, 0.08])
            rax.set_title(emotion, fontsize=10, fontweight='bold')
            self.radio_axes.append(rax)

            rb = RadioButtons(rax, REGULAR_LABELS)
            rb.on_clicked(self.make_state_callback(i))
            self.radio_controls.append(rb)

            b_ax = plt.axes([0.94, y + 0.01, 0.03, 0.06])
            b = Button(b_ax, "E", color='lightgrey', hovercolor='lightgreen')
            b.on_clicked(self.make_empathy_cb(i, b))
            self.empathy_controls.append(b)

        # LEFT SIDE: Quadrants
        quadrant_labels = ["Social", "Esteem", "Security", "Physical", "Self Actualization"]
        for i in range(5):
            ax_box = plt.axes([0.02, 0.75 - i * 0.12, 0.2, 0.1])
            ax_box.set_title(quadrant_labels[i], fontsize=10, fontweight='bold')

            if i < 4:
                q_labels = ["N/A", "Unmet", "Met"]
            else:
                q_labels = ["N/A", "Met"]

            rb = RadioButtons(ax_box, q_labels)
            rb.on_clicked(self.make_quadrant_callback(i))
            self.quadrant_controls.append(rb)

        # BOTTOM BUTTONS
        button_width = 0.10
        button_height = 0.05
        spacing = 0.02
        total_width = 4 * button_width + 3 * spacing
        start_x = 0.5 - total_width / 2
        button_y = 0.03

        self.reset_button = Button(plt.axes([start_x, button_y, button_width, button_height]),
                                   "Reset", color='lightgrey', hovercolor='lightgreen')
        self.reset_button.on_clicked(self.reset_all)

        self.add_button = Button(plt.axes([start_x + button_width + spacing, button_y, button_width, button_height]),
                                 "Add", color='lightgrey', hovercolor='lightblue')
        self.add_button.on_clicked(self.add_current_config)

        self.spirit_button = Button(plt.axes([start_x + 2*(button_width + spacing), button_y, button_width, button_height]),
                                    "Spirit", color='lightgrey', hovercolor='lightblue')
        self.spirit_button.on_clicked(self.toggle_spirit)

        self.save_button = Button(plt.axes([start_x + 3*(button_width + spacing), button_y, button_width, button_height]),
                                  "Save", color='lightgrey', hovercolor='lightgreen')
        self.save_button.on_clicked(self.save_sequence)

        self.counter_ax = plt.axes([0.5 - 0.05, 0.08, 0.1, 0.03])
        self.counter_ax.axis('off')
        self.counter_text = self.counter_ax.text(0.5, 0.5, 'Configs: 0',
                                            ha='center', va='center',
                                            fontsize=10, fontweight='bold')

        self.fig.subplots_adjust(bottom=0.08)
        self.draw()

    def make_state_callback(self, index):
        def callback(label):
            if self.spirit:
                mapping = {"N/A": 0, "Ego": 1, "Shadow": 2}
                self.spirit_triangle_states[index] = mapping[label]
            else:
                mapping = {"N/A": 0, "Expressed": 1, "Suppressed": 2, "Repressed": 3}
                self.states[index] = mapping[label]
            self.draw()
        return callback

    def make_quadrant_callback(self, quadrant):
        def callback(label):
            if quadrant < 4:
                mapping = {"N/A": 0, "Unmet": 1, "Met": 2}
            else:
                mapping = {"N/A": 0, "Met": 1}
            self.quadrants[quadrant] = mapping[label]
            self.draw()
        return callback

    def make_empathy_cb(self, idx, button):
        def callback(event):
            if self.spirit:
                self.spirit_empathy[idx] = not self.spirit_empathy[idx]
                button.color = 'green' if self.spirit_empathy[idx] else 'lightgrey'
                button.hovercolor = 'green' if self.spirit_empathy[idx] else 'lightgreen'
            else:
                self.empathy[idx] = not self.empathy[idx]
                button.color = 'green' if self.empathy[idx] else 'lightgrey'
                button.hovercolor = 'green' if self.empathy[idx] else 'lightgreen'
            self.draw()
        return callback

    def toggle_spirit(self, event):
        self.spirit = not self.spirit
        color = 'lightblue' if self.spirit else 'lightgrey'
        self.spirit_button.color = color
        self.spirit_button.hovercolor = color

        for i in range(8):
            rax = self.radio_axes[i]
            
            rax.clear()
            
            if self.spirit:
                rax.set_title(SHADOW_EMOTIONS[i], fontsize=10, fontweight='bold')
                rax.set_facecolor('lightblue')
                rax.patch.set_alpha(0.1)
            else:
                rax.set_title(EMOTIONS[i], fontsize=10, fontweight='bold')
                rax.set_facecolor('none')
                rax.patch.set_alpha(0)
            
            if self.spirit:
                new_labels = SPIRIT_LABELS
                current_active = self.spirit_triangle_states[i]
                new_active = current_active if current_active < len(new_labels) else 0
            else:
                new_labels = REGULAR_LABELS
                current_active = self.states[i]
                new_active = current_active if current_active < len(new_labels) else 0
            
            new_rb = RadioButtons(rax, new_labels)
            new_rb.on_clicked(self.make_state_callback(i))
            new_rb.set_active(new_active)
            self.radio_controls[i] = new_rb
            
            if self.spirit:
                button_color = 'green' if self.spirit_empathy[i] else 'lightgrey'
            else:
                button_color = 'green' if self.empathy[i] else 'lightgrey'
            self.empathy_controls[i].color = button_color
            self.empathy_controls[i].hovercolor = button_color
        
        self.draw()

    def reset_all(self, event):
        self.states = [0] * 8
        self.empathy = [False] * 8
        self.quadrants = {i: 0 for i in range(5)}
        self.spirit = False
        self.spirit_triangle_states = [0] * 8
        self.spirit_empathy = [False] * 8
        self.saved_configs = []  # Clear the saved configurations count
        self.spirit_button.color = 'lightgrey'
        self.spirit_button.hovercolor = 'lightblue'

        for i in range(8):
            rax = self.radio_axes[i]
            rax.clear()
            rax.set_title(EMOTIONS[i], fontsize=10, fontweight='bold')
            rax.set_facecolor('none')
            rax.patch.set_alpha(0)
            
            new_rb = RadioButtons(rax, REGULAR_LABELS)
            new_rb.on_clicked(self.make_state_callback(i))
            new_rb.set_active(0)
            self.radio_controls[i] = new_rb

        for b in self.empathy_controls:
            b.color = 'lightgrey'
            b.hovercolor = 'lightgreen'
        for rb in self.quadrant_controls:
            rb.set_active(0)
        
        self.counter_text.set_text('Configs: 0')  # Reset the counter display

        self.draw()

    def add_current_config(self, event):
        config = {
            'states': self.states.copy(),
            'empathy': self.empathy.copy(),
            'quadrants': self.quadrants.copy(),
            'spirit': self.spirit,
            'spirit_triangle_states': self.spirit_triangle_states.copy(),
            'spirit_empathy': self.spirit_empathy.copy()
        }
        self.saved_configs.append(config)
        self.counter_text.set_text(f'Configs: {len(self.saved_configs)}')
        self.draw()

    def save_sequence(self, event):
        # If there's a current unsaved config (not empty), add it first
        if (any(self.states) or any(self.empathy) or 
            any(v for v in self.quadrants.values()) or 
            any(self.spirit_triangle_states)):
            # But only add if it's not an empty config
            is_empty = (all(s == 0 for s in self.states) and 
                       all(not e for e in self.empathy) and
                       all(v == 0 for v in self.quadrants.values()) and
                       all(s == 0 for s in self.spirit_triangle_states) and
                       not self.spirit)
            if not is_empty:
                self.add_current_config(None)

        if not self.saved_configs:
            print("No configurations to save.")
            return

        file_path = ask_save_filename()
        if not file_path:
            return

        num_configs = len(self.saved_configs)
        cols = min(5, num_configs)
        rows = (num_configs + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(cols * 3.5, rows * 3.5))
        if rows == 1 and cols == 1:
            axes = np.array([[axes]])
        elif rows == 1 or cols == 1:
            axes = axes.reshape(rows, cols)

        axes_flat = axes.flatten()

        for idx, config in enumerate(self.saved_configs):
            if idx < len(axes_flat):
                ax = axes_flat[idx]
                ax.set_aspect('equal')
                ax.axis('off')
                # Show sequence number for all configs in a multi-config save
                # For single config, show no number (as requested)
                if num_configs > 1:
                    # Number only non-last configs
                    if idx < num_configs - 1:
                        draw_star(ax, config['states'], config['empathy'],
                                  config['quadrants'], config.get('spirit', False),
                                  config.get('spirit_triangle_states', [0]*8),
                                  idx + 1)  # Show number for all except the last
                    else:
                        # Last config - no number
                        draw_star(ax, config['states'], config['empathy'],
                                  config['quadrants'], config.get('spirit', False),
                                  config.get('spirit_triangle_states', [0]*8),
                                  None)
                else:
                    # Single config - no number
                    draw_star(ax, config['states'], config['empathy'],
                              config['quadrants'], config.get('spirit', False),
                              config.get('spirit_triangle_states', [0]*8),
                              None)

        for idx in range(num_configs, len(axes_flat)):
            axes_flat[idx].axis('off')

        plt.tight_layout()
        fig.savefig(file_path, dpi=300, transparent=True, bbox_inches='tight',
                    pad_inches=0.1, facecolor='none')
        plt.close(fig)

        # Reset saved configs and counter after saving
        self.saved_configs = []
        self.counter_text.set_text('Configs: 0')
        print(f"Sequence of {num_configs} soul states saved to {file_path}")

    def draw(self):
        draw_star(self.ax, self.states, self.empathy, self.quadrants, self.spirit, self.spirit_triangle_states)
        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    editor = DiagramEditor()
    plt.show()
