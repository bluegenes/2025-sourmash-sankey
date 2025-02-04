import csv
import argparse
import plotly.graph_objects as go

def save_sankey_diagram(fig, output_file):
    if output_file:
        if output_file.endswith(".html"):
            fig.write_html(output_file)
            print(f"Saved interactive HTML: {output_file}")
        elif output_file.endswith((".png", ".jpg", ".jpeg", ".pdf", ".svg")):
            fig.write_image(output_file)
            print(f"Saved image file: {output_file}")
        else:
            print("Unsupported file format. Use .html, .png, .jpg, .jpeg, .pdf, or .svg.")
    else:
        fig.show()  # Show the plot if no output file is specified

def process_taxmetagenome_csv(summary_csv):
    nodes = []  # List of unique taxonomy nodes
    node_map = {}  # Map taxonomic label to index
    links = []  # List of link connections with flow values
    hover_texts = []  # Custom hover text for percentages
    processed_lineages = set()  # Tracks added lineage links

    # Read CSV file
    with open(summary_csv, 'r') as file:
        reader = csv.DictReader(file)
        data = list(reader)

    # Process each row in the dataset
    for row in data:
        fraction = float(row["fraction"]) * 100  # Convert to percentage
        lineage_parts = row["lineage"].split(";")  # Taxonomic hierarchy

        # Iterate through lineage levels and create source-target links
        for i in range(len(lineage_parts) - 1):
            source_label = lineage_parts[i].strip()
            target_label = lineage_parts[i + 1].strip()

            # Since 'tax metagenome' is already summarize, skip duplicates to prevent overcounting
            if (source_label, target_label) in processed_lineages:
                continue

            # Assign indices to nodes
            if source_label not in node_map:
                node_map[source_label] = len(nodes)
                nodes.append(source_label)

            if target_label not in node_map:
                node_map[target_label] = len(nodes)
                nodes.append(target_label)

            # Create a link between source and target
            links.append({
                "source": node_map[source_label],
                "target": node_map[target_label],
                "value": fraction
            })
            processed_lineages.add((source_label, target_label))  # Track added links
            hover_texts.append(f"{source_label} → {target_label}<br>{fraction:.2f}%")

    return nodes, links, hover_texts

def process_taxannotate_csv(withlineages_csv):
    nodes = []  # List of unique taxonomy nodes
    node_map = {}  # Map taxonomic label to index
    links = []  # List of link connections with flow values
    hover_texts = []  # Custom hover text for percentages

    # Read CSV file
    with open(withlineages_csv, 'r') as file:
        reader = csv.DictReader(file)
        data = list(reader)

    # Process each row in the dataset
    for row in data:
        fraction = float(row["f_unique_weighted"]) * 100  # Convert to percentage
        lineage_parts = row["lineage"].split(";")  # Taxonomic hierarchy

        # Iterate through lineage levels and create source-target links
        for i in range(len(lineage_parts) - 1):
            source_label = lineage_parts[i].strip()
            target_label = lineage_parts[i + 1].strip()

            # Assign indices to nodes
            if source_label not in node_map:
                node_map[source_label] = len(nodes)
                nodes.append(source_label)

            if target_label not in node_map:
                node_map[target_label] = len(nodes)
                nodes.append(target_label)

            # Create a link between source and target
            links.append({
                "source": node_map[source_label],
                "target": node_map[target_label],
                "value": fraction
            })
            hover_texts.append(f"{source_label} → {target_label}<br>{fraction:.2f}%")

    return nodes, links, hover_texts


def main(args):

    # Build sankey links appropriately based on input file type
    if args.summary_csv:
        # Check if the required headers are present
        required_headers = ["fraction", "lineage"]
        if not all(header in header for header in required_headers):
            raise ValueError("Expected headers 'fraction' and 'lineage' not found. Is this a 'csv_summary' file from 'sourmash tax metagenome'?")
        nodes, links, hover_texts = process_taxmetagenome_csv(args.summary_csv)
        base_title = args.summary_csv.rsplit(".summarized.csv")[0]
    elif args.annotate_csv:
        # Check if the required headers are present
        required_headers = ["f_unique_weighted", "lineage"]
        if not all(header in header for header in required_headers):
            raise ValueError("Expected headers 'f_unique_weighted' and 'lineage' not found. Is this a 'with-lineages' file from 'sourmash tax annotate'?")
        nodes, links, hover_texts = process_taxannotate_csv(args.annotate_csv)
        base_title = args.annotate_csv.rsplit(".with-lineages.csv")[0]

    # Create Sankey diagram
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            label=nodes
        ),
        link=dict(
            source=[link["source"] for link in links],
            target=[link["target"] for link in links],
            value=[link["value"] for link in links],
            customdata=hover_texts,
            hovertemplate="%{customdata}<extra></extra>"  # Use custom hover text
        )
    ))

    if args.title:
        title = args.title
    else:
        title = base_title 
    fig.update_layout(title_text=f"{title}",
                      font_size=10,
                      autosize=False,
                      width=1500,  # Increase width
                      height=900   # Increase height
                    )

    # Save output based on file extension
    save_sankey_diagram(fig, args.output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a Sankey diagram from a taxonomy summary CSV file.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--summary-csv", type=str, help="Path to csv_summary generated by running 'sourmash tax metagenome' on a sourmash gather csv")
    group.add_argument("--annotate-csv", type=str, help="Path to 'with-lineages' file generated by running 'sourmash tax annotate' on a sourmash gather csv")
    parser.add_argument("-o", "--output", type=str, help="output file for alluvial flow diagram")
    parser.add_argument("--title", type=str, help="Plot title (default: use input filename)")
    args = parser.parse_args()
    
    main(args)


