from opyml import OPML


def parse_outlines(input):
    output = []
    for outline in input.outlines:
        output = output + parse_outlines(outline)
        if outline.type == 'rss':
            output.append(outline)
    return output


with open('feeds.opml', 'r') as f:
    data = f.read()
    doc = OPML.from_xml(data)
    print(doc.body.outlines[0].outlines[0].type)
    outlines = parse_outlines(doc.body)
    for outline in outlines:
        print(outline.title)
    print(len(outlines))
