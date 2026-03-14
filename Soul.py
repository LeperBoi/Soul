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
    "Joy","Trust","Fear","Surprise",
    "Sorrow","Disgust","Anger","Anticipation"
]

# =====================================================
# GEOMETRY
# =====================================================

def rotate(points, angle):
    rot = np.array([
        [np.cos(angle), -np.sin(angle)],
        [np.sin(angle),  np.cos(angle)]
    ])
    return np.dot(points, rot.T)

def transform(points, angle, scale, x, y):
    pts = rotate(points, angle)
    pts *= scale
    pts[:,0] += x
    pts[:,1] += y
    return pts

# =====================================================
# THICK LINE
# =====================================================

def draw_thick_line(ax, x1, y1, x2, y2):
    dx = x2-x1
    dy = y2-y1
    length = np.sqrt(dx*dx+dy*dy)
    if length == 0:
        return
    dx/=length
    dy/=length
    px = -dy
    py = dx
    half = LINE_THICKNESS/2
    corners = [
        [x1+px*half,y1+py*half],
        [x1-px*half,y1-py*half],
        [x2-px*half,y2-py*half],
        [x2+px*half,y2+py*half]
    ]
    ax.add_patch(Polygon(corners,closed=True,color="black"))

# =====================================================
# SYMBOLS
# =====================================================

def draw_symbol(ax, x, y, dx, dy, state, empathized, abrahamic=False):
    angle = np.arctan2(dy, dx)
    size = SYMBOL_SIZE

    # EXPRESSED
    if state == 1:
        if abrahamic:
            glow = Circle((x,y), SYMBOL_SIZE*1.5, color='gold', alpha=0.4)
            ax.add_patch(glow)
        else:
            arrow = np.array([[1.0,0.0],[-0.7,0.6],[-0.7,-0.6]])
            pts = transform(arrow, angle, size, x, y)
            ax.add_patch(Polygon(pts,closed=True,color="black"))

    # SUPPRESSED
    if state == 2:
        arrow = np.array([[1.0,0.0],[-0.7,0.6],[-0.7,-0.6]])
        pts = transform(arrow, angle, size, x, y)
        ax.add_patch(Polygon(pts,closed=True,color="black"))
        diode = np.array([[0.8,0.7],[0.8,-0.7]])
        line = transform(diode, angle, size, x, y)
        draw_thick_line(ax,line[0][0],line[0][1],line[1][0],line[1][1])

    # REPRESSED (|-|)
    if state == 3:
        spacing = 1.0
        for offset in [-spacing/2, spacing/2]:
            bars = np.array([[offset, 0.9], [offset, -0.9]])
            bar = transform(bars, angle, size, x, y)
            draw_thick_line(ax, bar[0][0], bar[0][1], bar[1][0], bar[1][1])
        horizontal = np.array([[-spacing/2, 0], [spacing/2, 0]])
        h_line = transform(horizontal, angle, size, x, y)
        draw_thick_line(ax, h_line[0][0], h_line[0][1], h_line[1][0], h_line[1][1])

    # EMPATHY
    if empathized:
        # Empathy circle is gold in Abrahamic mode, black otherwise
        circle_color = 'gold' if abrahamic else 'black'
        ax.add_patch(Circle((x,y), SYMBOL_SIZE*1.25, fill=False, linewidth=6, color=circle_color))

# =====================================================
# QUADRANT LINES
# =====================================================

def draw_quadrant_line(ax, quadrant, style):
    leg_center = 0.5
    leg_outer = 0.56  # Adjusted to match outer edge of thick line
    
    if quadrant == 0:  # Top-right quadrant
        if style == 1:  # Unmet - diagonal line
            draw_thick_line(ax, leg_center, 0, 0, leg_center)
        elif style == 2:  # Met - filled triangle matching OUTER edge
            pts = np.array([[0,0], [leg_outer, 0], [0, leg_outer]])
            ax.add_patch(Polygon(pts, closed=True, color="black"))
            
    elif quadrant == 1:  # Top-left quadrant
        if style == 1:  # Unmet - diagonal line
            draw_thick_line(ax, -leg_center, 0, 0, leg_center)
        elif style == 2:  # Met - filled triangle
            pts = np.array([[0,0], [-leg_outer, 0], [0, leg_outer]])
            ax.add_patch(Polygon(pts, closed=True, color="black"))
            
    elif quadrant == 2:  # Bottom-left quadrant
        if style == 1:  # Unmet - diagonal line
            draw_thick_line(ax, -leg_center, 0, 0, -leg_center)
        elif style == 2:  # Met - filled triangle
            pts = np.array([[0,0], [-leg_outer, 0], [0, -leg_outer]])
            ax.add_patch(Polygon(pts, closed=True, color="black"))
            
    elif quadrant == 3:  # Bottom-right quadrant
        if style == 1:  # Unmet - diagonal line
            draw_thick_line(ax, leg_center, 0, 0, -leg_center)
        elif style == 2:  # Met - filled triangle
            pts = np.array([[0,0], [leg_outer, 0], [0, -leg_outer]])
            ax.add_patch(Polygon(pts, closed=True, color="black"))

# =====================================================
# STAR DRAWING
# =====================================================

def draw_star(ax, states, empathy, quadrants=None, abrahamic=False):
    ax.clear()

    if abrahamic:
        angles = np.linspace(0,2*np.pi,16,endpoint=False)
        radii = np.array([1.0 if i%2==0 else 0.4 for i in range(16)])
        x = radii*np.cos(angles)
        y = radii*np.sin(angles)
        star = Polygon(np.column_stack([x,y]), closed=True, facecolor='gold', edgecolor='black', linewidth=2)
        ax.add_patch(star)
    else:
        radius=1.0
        angles=np.linspace(np.pi/2,np.pi/2-2*np.pi,8,endpoint=False)
        x=radius*np.cos(angles)
        y=radius*np.sin(angles)
        for i in range(8):
            j=(i+4)%8
            draw_thick_line(ax,x[i],y[i],x[j],y[j])

    for i in range(8):
        if abrahamic:
            tip_idx=i*2
            dx=x[tip_idx]; dy=y[tip_idx]
            norm=np.sqrt(dx*dx+dy*dy)
            dx/=norm; dy/=norm
            draw_symbol(ax, x[tip_idx], y[tip_idx], dx, dy, states[i], empathy[i], abrahamic=True)
        else:
            dx=x[i]; dy=y[i]
            norm=np.sqrt(dx*dx+dy*dy)
            dx/=norm; dy/=norm
            draw_symbol(ax, x[i], y[i], dx, dy, states[i], empathy[i], abrahamic=False)

    if quadrants:
        for q, style in quadrants.items():
            if style>0:
                if q<4:
                    draw_quadrant_line(ax,q,style)
                elif q==4:
                    # Center circle is gold in Abrahamic mode, black otherwise
                    circle_color = 'gold' if abrahamic else 'black'
                    ax.add_patch(Circle((0,0),0.6,fill=False,linewidth=6,color=circle_color))

    # Center dot is always black
    ax.plot(0,0,'o',color='black',markersize=10)
    ax.set_xlim(-1.6,1.6)
    ax.set_ylim(-1.6,1.6)
    ax.set_aspect("equal")
    ax.axis("off")

# =====================================================
# FILE SAVE DIALOG
# =====================================================

def ask_save_filename():
    """Open a file dialog to ask where to save the image"""
    # Create root window and hide it
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)  # Bring dialog to front
    
    # Generate default filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"Soul_State_{timestamp}.png"
    
    # Ask for save location
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[
            ("PNG files", "*.png"),
            ("All files", "*.*")
        ],
        initialfile=default_filename,
        title="Save Soul State As"
    )
    
    # Clean up
    root.destroy()
    
    return file_path

# =====================================================
# DIAGRAM EDITOR
# =====================================================

class DiagramEditor:
    def __init__(self):
        self.states=[0]*8
        self.empathy=[False]*8
        self.quadrants={i:0 for i in range(5)}
        self.abrahamic=False

        self.radio_controls=[]
        self.empathy_controls=[]
        self.quadrant_controls=[]

        # Create figure with toolbar disabled
        plt.rcParams['toolbar'] = 'None'
        self.fig=plt.figure(figsize=(14,9))
        
        # Set the window title
        self.fig.canvas.manager.set_window_title("Soul")
        
        self.ax=plt.axes([0.3,0.1,0.4,0.8])
        labels=["N/A","Expressed","Suppressed","Repressed"]

        # RIGHT SIDE CONTROLS
        for i,emotion in enumerate(EMOTIONS):
            y=0.88-i*0.1
            
            # Create main radio button box for emotion
            rax=plt.axes([0.72,y,0.22,0.08])
            rax.set_title(emotion,fontsize=10,fontweight='bold')
            rb=RadioButtons(rax,labels)
            rb.on_clicked(self.make_state_callback(i))
            self.radio_controls.append(rb)
            
            # Create empathy button INSIDE the right side of the same box
            # Position it at the right edge of the radio button box
            b_ax = plt.axes([0.94, y+0.01, 0.03, 0.06])
            b = Button(b_ax, "E", color='lightgrey', hovercolor='lightgreen')
            b.on_clicked(self.make_empathy_cb(i,b))
            self.empathy_controls.append(b)

        # LEFT BOXES - Updated labels
        quadrant_labels = ["Social", "Esteem", "Security", "Physical", "Self Actualization"]
        for i in range(5):
            ax_box = plt.axes([0.02,0.75 - i*0.12, 0.2, 0.1])
            ax_box.set_title(quadrant_labels[i], fontsize=10, fontweight='bold')
            if i<4: 
                labels_quad=["N/A","Unmet","Met"]
            else: 
                labels_quad=["N/A","Met"]  # Self Actualization only has N/A and Met
            rb = RadioButtons(ax_box, labels_quad)
            rb.on_clicked(self.make_quadrant_callback(i))
            self.quadrant_controls.append(rb)

        # BOTTOM BUTTONS - Perfectly centered
        button_width = 0.10
        button_height = 0.05
        spacing = 0.02
        
        # Calculate positions for perfect centering
        total_width = 3*button_width + 2*spacing
        start_x = 0.5 - total_width/2
        
        # Position buttons slightly higher
        button_y = 0.03
        
        # Reset button
        reset_ax = plt.axes([start_x, button_y, button_width, button_height])
        self.reset_button = Button(reset_ax, "Reset", color='lightgrey', hovercolor='lightgreen')
        self.reset_button.on_clicked(self.reset_all)

        # Abrahamic Mode button
        mode_ax = plt.axes([start_x + button_width + spacing, button_y, button_width, button_height])
        self.mode_button = Button(mode_ax, "Abrahamic", color='lightgrey', hovercolor='lightgreen')
        self.mode_button.on_clicked(self.toggle_abrahamic)

        # Save button
        save_ax = plt.axes([start_x + 2*(button_width + spacing), button_y, button_width, button_height])
        self.save_button = Button(save_ax, "Save", color='lightgrey', hovercolor='lightgreen')
        self.save_button.on_clicked(self.save_current_symbol)

        # Adjust figure to remove any bottom menu bar space
        self.fig.subplots_adjust(bottom=0.08)

        self.draw()

    def make_state_callback(self,index):
        def callback(label):
            mapping={"N/A":0,"Expressed":1,"Suppressed":2,"Repressed":3}
            self.states[index]=mapping[label]
            self.draw()
        return callback

    def make_quadrant_callback(self,quadrant):
        def callback(label):
            if quadrant < 4:  # Quadrants 0-3 (Social, Esteem, Security, Physical)
                mapping={"N/A":0,"Unmet":1,"Met":2}
            else:  # Quadrant 4 (Self Actualization)
                mapping={"N/A":0,"Met":1}  # Map "Met" to value 1 for the center circle
            self.quadrants[quadrant] = mapping[label]
            self.draw()
        return callback

    def make_empathy_cb(self, idx, button):
        def callback(event):
            self.empathy[idx] = not self.empathy[idx]
            button.color = 'green' if self.empathy[idx] else 'lightgrey'
            button.hovercolor = 'green' if self.empathy[idx] else 'lightgreen'
            self.draw()
        return callback

    def toggle_abrahamic(self,event):
        self.abrahamic = not self.abrahamic
        color = 'gold' if self.abrahamic else 'lightgrey'
        self.mode_button.color=color
        self.mode_button.hovercolor=color
        self.draw()

    def reset_all(self,event):
        self.states=[0]*8
        self.empathy=[False]*8
        self.quadrants={i:0 for i in range(5)}
        for rb in self.radio_controls: rb.set_active(0)
        for b in self.empathy_controls: b.color='lightgrey'; b.hovercolor='lightgreen'
        for rb in self.quadrant_controls: rb.set_active(0)
        self.draw()

    def draw(self):
        draw_star(self.ax,self.states,self.empathy,self.quadrants,self.abrahamic)
        self.fig.canvas.draw_idle()

    # =====================================================
    # SAVE SOUL STATE WITH FILE DIALOG
    # =====================================================
    def save_current_symbol(self, event):
        # Ask user where to save the file
        file_path = ask_save_filename()
        
        # If user cancelled the dialog, don't save
        if not file_path:
            print("Save cancelled")
            return

        # Create a new figure for saving
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_facecolor('none')  # Transparent background
        fig.patch.set_alpha(0)    # Transparent figure background

        # Draw the complete star with all current settings
        draw_star(ax, self.states, self.empathy, self.quadrants, self.abrahamic)

        # Save with tight bounding box and no padding
        fig.savefig(file_path, 
                   dpi=300, 
                   transparent=True, 
                   bbox_inches='tight', 
                   pad_inches=0,
                   facecolor='none',
                   edgecolor='none')
        
        plt.close(fig)
        print(f"Soul state saved to {file_path}")

# =====================================================
# MAIN
# =====================================================

if __name__=="__main__":
    editor=DiagramEditor()
    plt.show()
