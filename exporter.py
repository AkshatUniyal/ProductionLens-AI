from fpdf import FPDF
import json
from datetime import datetime

class Exporter:
    def __init__(self):
        pass

    def generate_pdf(self, result_dict):
        pdf = FPDF()
        pdf.add_page()
        
        # --- HEADER & LOGO ---
        pdf.set_fill_color(30, 58, 138) # Dark Blue Header
        pdf.rect(0, 0, 210, 40, "F")
        
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(15, 12)
        pdf.cell(0, 10, "ProductionLens AI", ln=True)
        
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(147, 197, 253)
        pdf.set_xy(15, 22)
        pdf.cell(0, 10, "Enterprise Readiness Report", ln=True)
        
        # --- PROJECT NAME TITLE ---
        pdf.set_xy(15, 45)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(30, 41, 59)
        project_name = result_dict.get('project_name') or " ".join(result_dict.get('input_summary', 'Audit Project').split()[:4])
        pdf.cell(0, 10, project_name, ln=True)
        
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 5, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(5)
        
        # --- READINESS METRICS ---
        score = result_dict.get('readiness_score', 0)
        if score >= 90:
            fill = (239, 246, 255); text_c = (37, 99, 235)
        elif score >= 75:
            fill = (236, 253, 245); text_c = (16, 185, 129)
        elif score >= 50:
            fill = (255, 251, 235); text_c = (245, 158, 11)
        else:
            fill = (254, 242, 242); text_c = (239, 68, 68)
            
        pdf.set_fill_color(*fill)
        pdf.rect(15, pdf.get_y(), 180, 25, "F")
        pdf.set_xy(20, pdf.get_y() + 5)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*text_c)
        pdf.cell(0, 6, f"Readiness Score: {score}/100", ln=True)
        
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(30, 41, 59)
        pdf.set_xy(20, pdf.get_y())
        pdf.cell(0, 8, f"Recommendation: {result_dict.get('recommendation', '')}", ln=True)
        pdf.ln(10)
        
        # --- EXECUTIVE SUMMARY ---
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 10, "Executive Summary", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(0, 6, result_dict.get('executive_summary', ''))
        pdf.ln(5)
        
        # --- STRATEGIC METRICS ---
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 10, "Strategic Metrics", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(0, 6, f"AI ROI Potential: {result_dict.get('roi_score', 'N/A')}/10", ln=True)
        pdf.cell(0, 6, f"Estimated Pilot Budget: {result_dict.get('estimated_pilot_cost', 'N/A')}", ln=True)
        pdf.ln(5)
        
        # --- 8-LENS PERFORMANCE BENCHMARK ---
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 10, "Lens Breakdown", ln=True)
        
        for lens in result_dict.get('lens_scores', []):
            if pdf.get_y() > 250:
                pdf.add_page()
                
            l_score = lens['score']
            if l_score >= 7:
                r,g,b = 16, 185, 129 # Green
                fr,fg,fb = 236, 253, 245 # Light green fill
            elif l_score >= 5:
                r,g,b = 245, 158, 11 # Yellow
                fr,fg,fb = 255, 251, 235 # Light amber fill
            else:
                r,g,b = 239, 68, 68 # Red
                fr,fg,fb = 254, 242, 242 # Light red fill
                
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(50, 8, lens['lens'])
            
            # Colored Score Badge
            pdf.set_fill_color(fr, fg, fb)
            pdf.set_text_color(r, g, b)
            pdf.cell(20, 8, f" {l_score}/10 ", ln=True, fill=True, align="C")
            
            # Multi-line rationale (Fixes truncation bug)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.set_x(20)
            pdf.multi_cell(170, 5, lens['rationale'])
            pdf.ln(3)
        
        # --- TECHNICAL GAP MAP (Checklist) ---
        if 'gaps' in result_dict:
            pdf.ln(5)
            if pdf.get_y() > 250: pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 10, "Technical Gap Map", ln=True)
            
            for item in result_dict['gaps']:
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(30, 41, 59)
                pdf.cell(0, 6, f"\x95 {item.get('feature', 'Feature')}", ln=True)
                pdf.set_x(20)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(100, 116, 139)
                pdf.multi_cell(0, 5, f"Current: {item.get('in_demo', '')} | Required: {item.get('in_production', '')}")
                pdf.ln(2)
        
        # --- PILOT ROADMAP ---
        if 'pilot_plan' in result_dict:
            pdf.ln(5)
            if pdf.get_y() > 250: pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 10, "Strategic Pilot Roadmap", ln=True)
            
            for idx, phase_text in enumerate(result_dict['pilot_plan']):
                pdf.set_fill_color(248, 250, 252)
                pdf.rect(15, pdf.get_y(), 180, 20, "F")
                pdf.set_xy(20, pdf.get_y() + 2)
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(37, 99, 235)
                pdf.cell(0, 6, f"Phase {idx+1}", ln=True)
                
                pdf.set_x(20)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(71, 85, 105)
                pdf.multi_cell(170, 5, phase_text)
                pdf.ln(6)
            
        return pdf.output()
