"""Office automation functions using pywin32 COM."""
import csv
import io
import os
from pathlib import Path
import win32com.client as win32
from . import llm_client


def generate_powerpoint_from_prompt(prompt):
    """
    Generate PowerPoint presentation from user prompt.

    LLM returns structured text describing slides.
    Parse and create .pptx via COM automation.

    Args:
        prompt: User's request for PowerPoint generation

    Returns:
        str: Status message

    Raises:
        Exception: If generation fails
    """
    try:
        # Prepare messages for LLM
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a PowerPoint generator. Return slide content in this exact format:\n"
                    "SLIDE: [Title]\n"
                    "[Bullet point 1]\n"
                    "[Bullet point 2]\n"
                    "...\n\n"
                    "Repeat for each slide. Keep it simple and structured."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Get LLM response
        response = llm_client.chat(messages)

        # Parse slides from response
        slides = []
        current_slide = None

        for line in response.strip().split('\n'):
            line = line.strip()
            if line.startswith('SLIDE:'):
                if current_slide:
                    slides.append(current_slide)
                title = line.replace('SLIDE:', '').strip()
                current_slide = {'title': title, 'bullets': []}
            elif line and current_slide is not None:
                # Remove markdown bullets if present
                bullet = line.lstrip('-*• ').strip()
                if bullet:
                    current_slide['bullets'].append(bullet)

        if current_slide:
            slides.append(current_slide)

        if not slides:
            raise Exception("No slides generated from LLM response")

        # Create PowerPoint via COM
        powerpoint = win32.Dispatch("PowerPoint.Application")
        powerpoint.Visible = True

        presentation = powerpoint.Presentations.Add()

        for slide_data in slides:
            # Add slide (ppLayoutText = 2)
            slide = presentation.Slides.Add(presentation.Slides.Count + 1, 2)

            # Set title
            slide.Shapes.Title.TextFrame.TextRange.Text = slide_data['title']

            # Add bullets
            if slide_data['bullets'] and len(slide.Shapes) > 1:
                text_frame = slide.Shapes[1].TextFrame
                text_range = text_frame.TextRange
                text_range.Text = '\n'.join(slide_data['bullets'])

        return f"PowerPoint created successfully with {len(slides)} slides!"

    except Exception as e:
        raise Exception(f"PowerPoint generation failed: {str(e)}")


def draft_word_report(prompt):
    """
    Draft Word report from user prompt.

    LLM returns markdown content.
    Insert into new Word document.

    Args:
        prompt: User's request for Word report

    Returns:
        str: Status message

    Raises:
        Exception: If generation fails
    """
    try:
        # Prepare messages for LLM
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a report writer. Generate a well-structured report in markdown format. "
                    "Use headings (# ## ###), bullet points, and paragraphs as appropriate."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Get LLM response
        response = llm_client.chat(messages)

        # Create Word document via COM
        word = win32.Dispatch("Word.Application")
        word.Visible = True

        doc = word.Documents.Add()
        selection = word.Selection

        # Parse markdown and insert into Word
        # Simple markdown parser for headings, bullets, and paragraphs
        for line in response.split('\n'):
            line_stripped = line.strip()

            if line_stripped.startswith('### '):
                # Heading 3
                selection.Style = "Heading 3"
                selection.TypeText(line_stripped.replace('### ', ''))
                selection.TypeParagraph()
            elif line_stripped.startswith('## '):
                # Heading 2
                selection.Style = "Heading 2"
                selection.TypeText(line_stripped.replace('## ', ''))
                selection.TypeParagraph()
            elif line_stripped.startswith('# '):
                # Heading 1
                selection.Style = "Heading 1"
                selection.TypeText(line_stripped.replace('# ', ''))
                selection.TypeParagraph()
            elif line_stripped.startswith('- ') or line_stripped.startswith('* '):
                # Bullet point
                selection.Style = "List Bullet"
                bullet_text = line_stripped.lstrip('-* ').strip()
                selection.TypeText(bullet_text)
                selection.TypeParagraph()
            elif line_stripped:
                # Normal paragraph
                selection.Style = "Normal"
                selection.TypeText(line_stripped)
                selection.TypeParagraph()
            else:
                # Empty line
                selection.TypeParagraph()

        return "Word report created successfully!"

    except Exception as e:
        raise Exception(f"Word report generation failed: {str(e)}")


def summarize_excel(prompt):
    """
    Summarize Excel data based on prompt.

    LLM returns plain-text summary only.
    Return summary to be displayed in chat.

    Args:
        prompt: User's request for Excel summary

    Returns:
        str: Summary text from LLM

    Raises:
        Exception: If summarization fails
    """
    try:
        # Prepare messages for LLM
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a data analyst. Provide a clear, concise summary in plain text. "
                    "No code, no formatting, just informative text."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Get LLM response
        response = llm_client.chat(messages)

        return response.strip()

    except Exception as e:
        raise Exception(f"Excel summarization failed: {str(e)}")


def generate_excel_file_from_prompt(prompt):
    """
    Generate Excel file from user prompt.

    LLM returns CSV only (no code fences, no prose).
    Parse CSV and populate new Excel workbook via COM.

    Args:
        prompt: User's request for Excel generation

    Returns:
        str: Status message

    Raises:
        Exception: If generation fails
    """
    try:
        # Prepare messages for LLM
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a CSV generator. Return ONLY valid CSV data with no explanation, "
                    "no code fences (```), no prose. Just raw CSV with headers in the first row."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Get LLM response
        response = llm_client.chat(messages)

        # Clean response (remove any accidental code fences)
        csv_data = response.strip()
        if csv_data.startswith('```'):
            lines = csv_data.split('\n')
            lines = [l for l in lines if not l.strip().startswith('```')]
            csv_data = '\n'.join(lines)

        # Parse CSV
        csv_reader = csv.reader(io.StringIO(csv_data))
        rows = list(csv_reader)

        if not rows:
            raise Exception("No CSV data generated")

        # Create Excel via COM
        excel = win32.Dispatch("Excel.Application")
        excel.Visible = True

        workbook = excel.Workbooks.Add()
        worksheet = workbook.Worksheets(1)

        # Populate cells
        for row_idx, row in enumerate(rows, start=1):
            for col_idx, value in enumerate(row, start=1):
                worksheet.Cells(row_idx, col_idx).Value = value

        # Format header row (bold)
        if rows:
            header_range = worksheet.Range(
                worksheet.Cells(1, 1),
                worksheet.Cells(1, len(rows[0]))
            )
            header_range.Font.Bold = True

        # Auto-fit columns
        worksheet.Columns.AutoFit()

        return f"Excel file created successfully with {len(rows)} rows!"

    except Exception as e:
        raise Exception(f"Excel generation failed: {str(e)}")
