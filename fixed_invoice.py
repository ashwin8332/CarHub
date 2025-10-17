from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from io import BytesIO
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Import the Order model
from .models import Order  # Use relative import if models.py is in the same directory
# If this fails, try: from carhub1.models import Order

# Check if reportlab is available
try:
    import reportlab
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

def fixed_download_invoice(order_id):
    """Download invoice PDF for an order"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    if not PDF_AVAILABLE:
        flash('PDF generation is not available. Please install reportlab: pip install reportlab', 'error')
        return redirect(url_for('my_orders'))
    
    # Create PDF
    buffer = BytesIO()
    
    # Set up the document with margins
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        leftMargin=36, 
        rightMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    
    # Get the width and height of the page
    width, height = A4
    
    # Create custom styles
    styles = getSampleStyleSheet()
    
    # Custom title style with CarHub colors
    title_style = styles['Title'].clone('CarHubTitle')
    title_style.fontName = 'Helvetica-Bold'
    title_style.fontSize = 24
    title_style.leading = 30
    title_style.alignment = 1  # Centered
    title_style.textColor = colors.HexColor('#7c4dff')  # Primary purple color
    
    # Custom header style
    header_style = styles['Heading2'].clone('CarHubHeader')
    header_style.fontName = 'Helvetica-Bold'
    header_style.fontSize = 14
    header_style.textColor = colors.HexColor('#23235b')  # Dark blue
    
    # Custom normal text style
    normal_style = styles['Normal'].clone('CarHubNormal')
    normal_style.fontName = 'Helvetica'
    normal_style.fontSize = 10
    normal_style.leading = 12
    
    # Custom bold text style
    bold_style = styles['Normal'].clone('CarHubBold')
    bold_style.fontName = 'Helvetica-Bold'
    bold_style.fontSize = 10
    bold_style.leading = 12
    
    # Generate invoice number (combination of order ID and timestamp)
    invoice_number = f"INV-{order.id}-{order.created_at.strftime('%Y%m%d')}"
    
    # Create story container for Flowables
    story = []
    
    # Create custom drawing function for the first page
    def add_first_page_elements(canvas, doc):
        # Save canvas state
        canvas.saveState()
        
        # Add watermark if paid
        if order.payment_status.lower() == 'paid':
            from flask import current_app
            watermark_path = os.path.join(current_app.root_path, 'static', 'paid_watermark.png')
            if os.path.exists(watermark_path):
                # Position the watermark in the center of the page with transparency
                canvas.saveState()
                canvas.setFillAlpha(0.15)  # Set transparency
                canvas.drawImage(watermark_path, width/2 - 100, height/2 - 100, 
                                width=200, height=200, preserveAspectRatio=True)
                canvas.restoreState()
        
        # Add logo in top left corner
        from flask import current_app
        logo_path = os.path.join(current_app.root_path, 'static', 'logo.png')
        if os.path.exists(logo_path):
            # Position logo at top left
            canvas.drawImage(logo_path, 36, height - 90, width=120, height=60, preserveAspectRatio=True)
        
        # Add company info in top right with enhanced styling
        company_info = [
            "CarHub Premium Auto",
            "123 Luxury Drive",
            "Automotive City, AC 98765",
            "support@carhub.com",
            "+1 (555) 123-4567",
            "www.carhub.com"
        ]
        
        # Draw a light background for company info
        canvas.setFillColor(colors.HexColor('#f8f9fa'))
        canvas.roundRect(width - 210, height - 100, 180, 80, 5, fill=1, stroke=0)
        
        text_obj = canvas.beginText(width - 200, height - 50)
        text_obj.setFont("Helvetica-Bold", 10)
        text_obj.setFillColor(colors.HexColor('#23235b'))
        text_obj.textLine(company_info[0])  # Company name in bold
        text_obj.setFont("Helvetica", 9)
        for line in company_info[1:]:
            text_obj.textLine(line)
        canvas.drawText(text_obj)
        
        # Add a decorative divider line below the header
        canvas.setStrokeColor(colors.HexColor('#7c4dff'))
        canvas.setLineWidth(2)
        canvas.line(36, height - 100, width - 36, height - 100)
        
        # Add a subtle shadow line
        canvas.setStrokeColor(colors.HexColor('#e6e6fa'))
        canvas.setLineWidth(1)
        canvas.line(36, height - 102, width - 36, height - 102)
        
        # Add invoice title with enhanced styling
        canvas.saveState()
        # Draw background for invoice title
        canvas.setFillColor(colors.HexColor('#f0f0ff'))
        canvas.roundRect(width/2 - 150, height - 145, 300, 30, 10, fill=1, stroke=0)
        
        canvas.setFont("Helvetica-Bold", 18)
        canvas.setFillColor(colors.HexColor('#23235b'))
        canvas.drawCentredString(width/2, height - 130, f"INVOICE #{invoice_number}")
        canvas.restoreState()
        
        # Generate QR code data - in a real implementation you'd use the qrcode library
        qr_data = f"INVOICE:{invoice_number}|ORDER:{order.id}|DATE:{order.created_at.strftime('%Y-%m-%d')}"
        
        # Draw a border around the QR code area
        canvas.setStrokeColor(colors.HexColor('#7c4dff'))
        canvas.roundRect(width - 100, 30, 60, 70, 5, fill=0, stroke=1)
        
        # Add QR code for invoice verification (simulated as a square with internal pattern)
        canvas.setFillColor(colors.black)
        canvas.rect(width - 90, 40, 50, 50, fill=0)
        
        # Add some patterns to simulate a QR code (this is just for visual effect)
        canvas.setFillColor(colors.black)
        for i in range(3):
            for j in range(3):
                if (i + j) % 2 == 0:  # Checker pattern
                    canvas.rect(width - 90 + i*16, 40 + j*16, 16, 16, fill=1)
        
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(width - 65, 30, "Scan to verify invoice")
        
        # Add footer with improved styling
        # Draw background for footer
        canvas.setFillColor(colors.HexColor('#f8f9fa'))
        canvas.roundRect(36, 30, width - 72, 50, 5, fill=1, stroke=0)
        
        # Add terms & conditions
        terms_text = canvas.beginText(46, 70)
        terms_text.setFont("Helvetica-Bold", 9)
        terms_text.setFillColor(colors.HexColor('#23235b'))
        terms_text.textLine("Terms & Conditions:")
        terms_text.setFont("Helvetica", 8)
        terms_text.setFillColor(colors.black)
        terms_text.textLine("Payment is due within 30 days. CarHub reserves ownership until full payment.")
        terms_text.textLine("For questions about this invoice, contact our customer support.")
        canvas.drawText(terms_text)
        
        # Add page number with decorative element
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(width - 36, 36, f"Page {doc.page}")
        
        # Add decorative element to page number
        canvas.setStrokeColor(colors.HexColor('#7c4dff'))
        canvas.line(width - 80, 34, width - 36, 34)
        
        # Restore canvas state
        canvas.restoreState()
    
    # Add spacer for logo area
    story.append(Spacer(1, 140))
    
    # Add date and customer info in two-column layout
    customer_data = [
        ["BILL TO:", "INVOICE DETAILS:"],
        [order.billing_name, f"Invoice Date: {order.created_at.strftime('%B %d, %Y')}"],
        [order.billing_address or "N/A", f"Due Date: {(order.created_at + timedelta(days=30)).strftime('%B %d, %Y')}"],
        [order.billing_email, f"Order ID: #{order.id}"],
        [order.billing_phone or "N/A", f"Transaction ID: {order.transaction_id}"]
    ]
    
    customer_table = Table(customer_data, colWidths=[doc.width/2 - 20, doc.width/2 - 20])
    customer_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONT', (0, 1), (-1, -1), 'Helvetica'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#23235b')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(customer_table)
    story.append(Spacer(1, 20))
    
    # Add vehicle info section with enhanced styling
    # Create a styled header with background
    vehicle_header = Paragraph("VEHICLE DETAILS", header_style)
    header_background = Table([[vehicle_header]], colWidths=[doc.width])
    header_background.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f0f0ff')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (0, 0), 10),
        ('RIGHTPADDING', (0, 0), (0, 0), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(header_background)
    story.append(Spacer(1, 10))
    
    # Create vehicle info table
    vehicle_info = []
    
    # Header row
    vehicle_info.append(["ITEM", "DESCRIPTION", "PRICE"])
    
    # Vehicle row with enhanced details
    if order.car:
        # Extract more details from the car if available
        car_details = [
            f"Make/Model: {order.car.name}",
            f"VIN: {order.car.vin if hasattr(order.car, 'vin') else 'Not Available'}",
            f"Color: {order.car.color if hasattr(order.car, 'color') else 'Standard'}"
        ]
        
        # Add year and engine details if available
        if hasattr(order.car, 'year'):
            car_details.insert(1, f"Year: {order.car.year}")
        
        if hasattr(order.car, 'engine'):
            car_details.append(f"Engine: {order.car.engine}")
        
        if hasattr(order.car, 'transmission'):
            car_details.append(f"Transmission: {order.car.transmission}")
            
        vehicle_info.append([
            "Premium Vehicle",
            "\n".join(car_details),
            f"${order.car.price:,.2f}" if hasattr(order.car, 'price') else "N/A"
        ])
    else:
        vehicle_info.append(["Vehicle", "Information Not Available", "N/A"])
    
    # Add fees and taxes
    base_price = order.car.price if order.car and hasattr(order.car, 'price') else (order.total_amount / 1.1)
    
    # Add delivery fee if applicable
    if hasattr(order, 'delivery_fee') and order.delivery_fee:
        delivery_fee = order.delivery_fee
    else:
        delivery_fee = base_price * 0.01  # Default 1% delivery fee
        
    vehicle_info.append(["Delivery Fee", "Vehicle delivery and handling", f"${delivery_fee:,.2f}"])
    vehicle_info.append(["Processing Fee", "Documentation and registration", f"${base_price * 0.02:,.2f}"])
    vehicle_info.append(["Tax", "Sales tax (8%)", f"${base_price * 0.08:,.2f}"])
    
    # Add subtotal line
    vehicle_info.append(["", "Subtotal", f"${base_price + delivery_fee + (base_price * 0.02) + (base_price * 0.08):,.2f}"])
    
    # Style the vehicle table
    vehicle_table = Table(vehicle_info, colWidths=[doc.width * 0.2, doc.width * 0.5, doc.width * 0.2])
    vehicle_table_style = TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c4dff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        
        # Vehicle row styling
        ('FONT', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),  # Right align all prices
        
        # Alternate row colors
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#f8f9fa')),
        
        # All cell borders
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#7c4dff')),
        
        # Subtotal row styling
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('FONT', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e6e6fa')),
        ('SPAN', (0, -1), (-2, -1)),  # Span the first two columns
        ('ALIGN', (-2, -1), (-2, -1), 'RIGHT'),  # Right align "Subtotal" text
    ])
    
    # Apply the style to the table and add to story
    vehicle_table.setStyle(vehicle_table_style)
    story.append(vehicle_table)
    story.append(Spacer(1, 20))
    
    # Create payment status indicator with color-coded badge
    status_color = colors.HexColor('#4CAF50') if order.payment_status.lower() == 'paid' else colors.HexColor('#FF9800')
    
    # Add payment summary header
    payment_header = Paragraph("PAYMENT SUMMARY", header_style)
    story.append(payment_header)
    story.append(Spacer(1, 10))
    
    # Create payment info with enhanced styling
    payment_data = [
        ["Payment Date:", order.created_at.strftime('%B %d, %Y')],
        ["Transaction ID:", order.transaction_id if hasattr(order, 'transaction_id') and order.transaction_id else "N/A"],
        ["Payment Method:", order.payment_method.replace('_', ' ').title()],
        ["Payment Status:", ""]  # Empty cell for custom status badge
    ]
    
    # Create the payment table
    payment_table = Table(payment_data, colWidths=[doc.width * 0.3, doc.width * 0.6])
    
    # Style the payment table
    payment_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, -1), 'Helvetica'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#23235b')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    
    story.append(payment_table)
    
    # Create a separate styled status badge
    status_text = order.payment_status.upper()
    status_table = Table([["", status_text]], colWidths=[10, doc.width * 0.3])
    status_table.setStyle(TableStyle([
        ('FONT', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
        ('BACKGROUND', (1, 0), (1, 0), status_color),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
        ('TOPPADDING', (1, 0), (1, 0), 6),
        ('BOTTOMPADDING', (1, 0), (1, 0), 6),
    ]))
    
    story.append(Spacer(1, -30))  # Negative spacer to position the badge at the right location
    story.append(status_table)
    story.append(Spacer(1, 20))
    
    # Create total amount section with gradient background
    total_info = [
        ["TOTAL AMOUNT DUE:", f"${order.total_amount:,.2f}"]
    ]
    
    # Apply different styling based on payment status
    if order.payment_status.lower() == 'paid':
        total_info[0][0] = "TOTAL AMOUNT PAID:"
    
    total_table = Table(total_info, colWidths=[doc.width * 0.5, doc.width * 0.4])
    total_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONT', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 16),  # Larger font for total amount
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#23235b')),  # Dark background
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),  # White text
        ('TOPPADDING', (0, 0), (1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (1, 0), 'MIDDLE'),
        ('BOX', (0, 0), (1, 0), 2, colors.HexColor('#7c4dff')),
    ]))
    
    story.append(total_table)
    story.append(Spacer(1, 30))
    
    # Create a styled box for the thank you message
    thank_you_paragraphs = [
        Paragraph("<b>Thank you for choosing CarHub Premium Auto!</b>", bold_style),
        Spacer(1, 5),
        Paragraph("We value your business and look forward to serving you again. Your satisfaction is our top priority.", normal_style),
        Spacer(1, 10),
        Paragraph("For any questions or concerns regarding this invoice, please contact our customer service team at <b>support@carhub.com</b> or call us at <b>+1 (555) 123-4567</b>.", normal_style)
    ]
    
    # Create a table for the thank you message with background
    thank_you_content = [[p] for p in thank_you_paragraphs]
    thank_you_table = Table(thank_you_content, colWidths=[doc.width - 80])
    thank_you_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#23235b')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e6e6fa')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
    ]))
    
    story.append(thank_you_table)
    
    # Add a promotional message if appropriate
    if order.payment_status.lower() == 'paid':
        story.append(Spacer(1, 20))
        promo_text = "As a valued customer, enjoy 10% off your next premium vehicle service by using code: <b>CARHUB10</b>"
        promo_para = Paragraph(promo_text, normal_style)
        promo_table = Table([[promo_para]], colWidths=[doc.width - 80])
        promo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#e6e6fa')),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#7c4dff')),
            ('TOPPADDING', (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (0, 0), (0, 0), 10),
        ]))
        story.append(promo_table)
    
    # Build the PDF with our custom header/footer
    doc.build(story, onFirstPage=add_first_page_elements, onLaterPages=add_first_page_elements)
    buffer.seek(0)
    
    # Log invoice download
    def log_user_activity(user_id, activity_type, description, metadata=None):
        # Placeholder: Implement logging logic here (e.g., save to database or file)
        pass

    log_user_activity(
        user_id=current_user.id,
        activity_type='invoice_downloaded',
        description=f'Downloaded invoice for order #{order.id}',
        metadata={
            'order_id': order.id,
            'invoice_number': invoice_number,
        }
    )
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=carhub_invoice_{order.id}.pdf'
    
    return response