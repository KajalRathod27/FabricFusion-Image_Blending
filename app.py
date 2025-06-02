import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import cv2
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from ttkthemes import ThemedTk

class SimpleFabricFusion:
    def __init__(self):
        self.fabric_image = None
        self.print_image = None
        self.blend_mode = "overlay"
        self.print_opacity = 0.7
        self.print_scale = 1.0
    
    def load_fabric(self, path):
        """Load and preprocess a fabric image."""
        fabric_img = cv2.imread(path)
        fabric_img = cv2.cvtColor(fabric_img, cv2.COLOR_BGR2RGB)
        return fabric_img
    
    def load_print(self, path):
        """Load and preprocess a print image."""
        # Check if the print has an alpha channel (transparency)
        if path.lower().endswith(('png', 'PNG')):
            print_img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if print_img.shape[2] == 4:  # Has alpha channel
                print_img = cv2.cvtColor(print_img, cv2.COLOR_BGRA2RGBA)
            else:
                print_img = cv2.cvtColor(print_img, cv2.COLOR_BGR2RGB)
        else:
            print_img = cv2.imread(path)
            print_img = cv2.cvtColor(print_img, cv2.COLOR_BGR2RGB)
        return print_img
    
    def resize_print(self, print_img, fabric_shape, scale=1.0):
        """Resize the print to match fabric dimensions with optional scaling."""
        target_height, target_width = fabric_shape[:2]
        
        # Apply scaling factor
        target_height = int(target_height * scale)
        target_width = int(target_width * scale)
        
        # Resize print
        resized_print = cv2.resize(print_img, (target_width, target_height))
        return resized_print
    
    def tile_print(self, print_img, fabric_shape):
        """Tile the print to cover the entire fabric."""
        h, w = fabric_shape[:2]
        print_h, print_w = print_img.shape[:2]
        
        # Calculate how many tiles needed
        tiles_h = int(np.ceil(h / print_h))
        tiles_w = int(np.ceil(w / print_w))
        
        # Create a canvas that's at least as large as the fabric
        canvas_h = tiles_h * print_h
        canvas_w = tiles_w * print_w
        
        # Initialize canvas with the appropriate number of channels
        if print_img.shape[2] == 4:  # Has alpha channel
            canvas = np.zeros((canvas_h, canvas_w, 4), dtype=print_img.dtype)
        else:
            canvas = np.zeros((canvas_h, canvas_w, 3), dtype=print_img.dtype)
        
        # Tile the print
        for i in range(tiles_h):
            for j in range(tiles_w):
                y_start = i * print_h
                y_end = (i + 1) * print_h
                x_start = j * print_w
                x_end = (j + 1) * print_w
                canvas[y_start:y_end, x_start:x_end] = print_img
        
        # Crop to fabric size
        tiled_print = canvas[:h, :w]
        return tiled_print
    
    def blend_images(self, fabric, print_img, blend_mode="overlay", opacity=0.7):
        """Apply blend mode for combining fabric and print."""
        # Check if print has alpha channel
        has_alpha = print_img.shape[2] == 4
        
        # Extract RGB and alpha channels if needed
        if has_alpha:
            print_rgb = print_img[:, :, :3]
            print_alpha = print_img[:, :, 3:4] / 255.0 * opacity
        else:
            print_rgb = print_img
            
        # Convert to float for blending calculations
        fabric_norm = fabric / 255.0
        print_norm = print_rgb / 255.0
        
        # Apply blend mode formula
        if blend_mode == "overlay":
            low = 2 * fabric_norm * print_norm
            high = 1 - 2 * (1 - fabric_norm) * (1 - print_norm)
            blended = np.where(fabric_norm < 0.5, low, high)
        elif blend_mode == "multiply":
            blended = fabric_norm * print_norm
        elif blend_mode == "screen":
            blended = 1 - (1 - fabric_norm) * (1 - print_norm)
        else:  # Default to overlay
            low = 2 * fabric_norm * print_norm
            high = 1 - 2 * (1 - fabric_norm) * (1 - print_norm)
            blended = np.where(fabric_norm < 0.5, low, high)
        
        # Apply alpha or opacity
        if has_alpha:
            result = fabric_norm * (1 - print_alpha) + blended * print_alpha
        else:
            result = fabric_norm * (1 - opacity) + blended * opacity
            
        return (result * 255).astype(np.uint8)
    
    def generate_fusion(self, fabric_img, print_img, blend_mode, opacity, scale):
        """Generate fused fabric with print."""
        # Resize print based on scale
        print_resized = self.resize_print(print_img, fabric_img.shape, scale)
        
        # Tile print to cover fabric
        print_tiled = self.tile_print(print_resized, fabric_img.shape)
        
        # Apply blend mode
        result = self.blend_images(fabric_img, print_tiled, blend_mode, opacity)
            
        return result
    
    def save_fusion(self, output_path, fused_image):
        """Save the fused image to output path."""
        fused_image_pil = Image.fromarray(fused_image)
        fused_image_pil.save(output_path)


class SimpleFabricFusionGUI:
    def __init__(self, root):
        """Initialize the GUI for SimpleFabricFusion."""
        self.root = root
        self.root.title("Simple Fabric Fusion")
        self.root.geometry("1000x700")
        
        self.fusion = SimpleFabricFusion()
        self.fabric_path = None
        self.print_path = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Create frames
        self.middle_frame = ttk.Frame(self.root, padding=10)
        self.middle_frame.pack(fill=tk.BOTH, expand=True)
        
        self.bottom_frame = ttk.Frame(self.root, padding=10)
        self.bottom_frame.pack(fill=tk.X)
        
        # Image display areas
        self.fabric_frame = ttk.LabelFrame(self.middle_frame, text="Fabric", padding=10)
        self.fabric_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.print_frame = ttk.LabelFrame(self.middle_frame, text="Print", padding=10)
        self.print_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.result_frame = ttk.LabelFrame(self.middle_frame, text="Result", padding=10)
        self.result_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        
        self.middle_frame.columnconfigure(0, weight=1)
        self.middle_frame.columnconfigure(1, weight=1)
        self.middle_frame.columnconfigure(2, weight=1)
        self.middle_frame.rowconfigure(0, weight=1)
        
        # Create canvas for images
        self.fabric_canvas = tk.Canvas(self.fabric_frame, bg="white")
        self.fabric_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.print_canvas = tk.Canvas(self.print_frame, bg="white")
        self.print_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.result_canvas = tk.Canvas(self.result_frame, bg="white")
        self.result_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Controls
        control_frame = ttk.LabelFrame(self.bottom_frame, text="Controls", padding=10)
        control_frame.pack(fill=tk.X)
        
        # Blend mode
        ttk.Label(control_frame, text="Blend Mode:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.blend_mode_var = tk.StringVar(value="overlay")
        blend_modes = ["overlay", "multiply", "screen"]
        ttk.Combobox(control_frame, textvariable=self.blend_mode_var, values=blend_modes, state="readonly").grid(row=0, column=1, padx=5, pady=5)
        
        # Opacity
        ttk.Label(control_frame, text="Opacity:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.opacity_var = tk.DoubleVar(value=0.7)
        opacity_scale = ttk.Scale(control_frame, from_=0.1, to=1.0, variable=self.opacity_var, orient=tk.HORIZONTAL)
        opacity_scale.grid(row=0, column=3, padx=5, pady=5)
        self.opacity_label = ttk.Label(control_frame, text="0.7")
        self.opacity_label.grid(row=0, column=4, padx=5, pady=5)
        opacity_scale.configure(command=self.update_opacity_label)
        
        # Scale
        ttk.Label(control_frame, text="Pattern Scale:").grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)
        self.scale_var = tk.DoubleVar(value=1.0)
        scale_scale = ttk.Scale(control_frame, from_=0.2, to=2.0, variable=self.scale_var, orient=tk.HORIZONTAL)
        scale_scale.grid(row=0, column=6, padx=5, pady=5)
        self.scale_label = ttk.Label(control_frame, text="1.0")
        self.scale_label.grid(row=0, column=7, padx=5, pady=5)
        scale_scale.configure(command=self.update_scale_label)
        
        # Buttons
        button_frame = ttk.Frame(self.bottom_frame, padding=10)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Select Fabric", command=self.select_fabric).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="Select Print", command=self.select_print).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(button_frame, text="Generate Fusion", command=self.generate_fusion).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(button_frame, text="Save Result", command=self.save_result).grid(row=0, column=3, padx=5, pady=5)
        
        # Make button row centered
        for i in range(4):
            button_frame.columnconfigure(i, weight=1)
    
    def update_opacity_label(self, value):
        """Update opacity label when slider changes."""
        self.opacity_label.configure(text=f"{float(value):.1f}")
    
    def update_scale_label(self, value):
        """Update scale label when slider changes."""
        self.scale_label.configure(text=f"{float(value):.1f}")
    
    def select_fabric(self):
        """Select a fabric image."""
        file_path = filedialog.askopenfilename(
            title="Select Fabric Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        
        if file_path:
            self.fabric_path = file_path
            self.fabric_img = self.fusion.load_fabric(file_path)
            self.display_image(self.fabric_img, self.fabric_canvas)
    
    def select_print(self):
        """Select a print image."""
        file_path = filedialog.askopenfilename(
            title="Select Print Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.PNG")]
        )
        
        if file_path:
            self.print_path = file_path
            self.print_img = self.fusion.load_print(file_path)
            self.display_image(self.print_img, self.print_canvas)
    
    def display_image(self, img, canvas):
        """Display image on canvas."""
        canvas.delete("all")
        
        if img is None:
            return
        
        # Convert to PIL Image
        if img.shape[2] == 4:  # Has alpha channel
            pil_img = Image.fromarray(img)
        else:
            pil_img = Image.fromarray(img)
        
        # Resize to fit canvas
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 300
            canvas_height = 300
        
        # Calculate new dimensions to maintain aspect ratio
        img_width, img_height = pil_img.size
        ratio = min(canvas_width / img_width, canvas_height / img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to PhotoImage
        from PIL import ImageTk
        photo = ImageTk.PhotoImage(pil_img)
        
        # Store reference to prevent garbage collection
        canvas.image = photo
        
        # Display on canvas
        canvas.create_image(canvas_width/2, canvas_height/2, image=photo, anchor=tk.CENTER)
    
    def generate_fusion(self):
        """Generate and display fusion result."""
        if not hasattr(self, 'fabric_img') or not hasattr(self, 'print_img'):
            messagebox.showwarning("Warning", "Please select both fabric and print images first.")
            return
        
        # Get current parameters
        blend_mode = self.blend_mode_var.get()
        opacity = self.opacity_var.get()
        scale = self.scale_var.get()
        
        # Generate fusion
        result = self.fusion.generate_fusion(
            self.fabric_img, 
            self.print_img, 
            blend_mode, 
            opacity, 
            scale
        )
        
        # Store result for saving
        self.result_img = result
        
        # Display result
        self.display_image(result, self.result_canvas)
    
    def save_result(self):
        """Save the fusion result."""
        if not hasattr(self, 'result_img'):
            messagebox.showwarning("Warning", "Please generate a fusion first.")
            return
        
        # Ask for save path
        file_path = filedialog.asksaveasfilename(
            title="Save Fusion Result",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")]
        )
        
        if file_path:
            self.fusion.save_fusion(file_path, self.result_img)
            messagebox.showinfo("Success", f"Saved fusion result to {file_path}")


def main():
    """Run the SimpleFabricFusion GUI application."""
    try:
        root = ThemedTk(theme="arc")  # Using themed Tk for better appearance
    except:
        # Fall back to regular Tk if themed Tk is not available
        root = tk.Tk()
        
    app = SimpleFabricFusionGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

#python -m venv venv OR
#venv\Scripts\activate 
#pip install numpy matplotlib pillow opencv-python tkinter ttkthemes
#pip install numpy opencv-python pillow matplotlib ttkthemes
#python app.py