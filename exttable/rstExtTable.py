""" ext-table

    Implementation of the ``ext-table`` reST-directive.

    Based on flat-table by Markus Heiser, original Copyright (C) 2016  Markus Heiser
    (see https://github.com/torvalds/linux/blob/master/Documentation/sphinx/rstFlatTable.py)
    :license:    GPL Version 2, June 1991 see linux/COPYING for details.

    The ``ext-table`` (:py:class:`ExtTable`) is a double-stage list similar to
    the ``list-table`` with some additional features, based on the linuxdoc
    ``flat-table`` directive:

    * *column-span*: with the role ``cspan`` a cell can be extended through
      additional columns
    * *row-span*: with the role ``rspan`` a cell can be extended through
      additional rows
    * *cell-class*: with the role ``cclass`` a list of classes can be attached
      to a cell
    * *auto span* rightmost cell of a table row over the missing cells on the
      right side of that table-row.  With Option ``:fill-cells:`` this behavior
      can be changed from *auto span* to *auto fill*, which automatically inserts
      (empty) cells instead of spanning the last cell.

    Options:
    * header-rows:   [int] count of header rows
    * stub-columns:  [int] count of stub columns
    * widths:        [[int] [int] ... ] widths of columns
    * fill-cells:    instead of autospann missing cells, insert missing cells
    * class:         [[string] [string] ...] classes to be added to table

    roles:
    * cspan: [int] additionale columns (*morecols*)
    * rspan: [int] additionale rows (*morerows*)
    * cclass: [string] [[string]...] classes to be attached
"""

# ==============================================================================
# imports
# ==============================================================================

from docutils import nodes
from docutils.parsers.rst import directives, roles
from docutils.parsers.rst.directives.tables import Table
from docutils.utils import SystemMessagePropagation

# ==============================================================================
# common globals
# ==============================================================================

__version__  = '1.0'

# ==============================================================================
def setup(app):
# ==============================================================================

    app.add_directive("ext-table", ExtTable)
    roles.register_local_role('cspan', c_span)
    roles.register_local_role('rspan', r_span)
    roles.register_local_role('cclass', c_class)

    return dict(
        version = __version__,
        parallel_read_safe = True,
        parallel_write_safe = True
    )

# ==============================================================================
def c_span(name, rawtext, text, lineno, inliner, options=None, content=None):
# ==============================================================================
    # pylint: disable=W0613

    options  = options if options is not None else {}
    content  = content if content is not None else []
    nodelist = [colSpan(span=int(text))]
    msglist  = []
    return nodelist, msglist

# ==============================================================================
def r_span(name, rawtext, text, lineno, inliner, options=None, content=None):
# ==============================================================================
    # pylint: disable=W0613

    options  = options if options is not None else {}
    content  = content if content is not None else []
    nodelist = [rowSpan(span=int(text))]
    msglist  = []
    return nodelist, msglist

def c_class(name, rawtext, text, lineno, inliner, options=None, content=None):
    options = options if options is not None else {}
    content = content if content is not None else []
    nodelist = [cellClass(classes=directives.class_option(text))]
    msglist = []
    return nodelist, msglist

# ==============================================================================
class rowSpan(nodes.General, nodes.Element): pass # pylint: disable=C0103,C0321
class colSpan(nodes.General, nodes.Element): pass # pylint: disable=C0103,C0321
class cellClass(nodes.General, nodes.Element): pass
# ==============================================================================

# ==============================================================================
class ExtTable(Table):
# ==============================================================================

    u"""ExtTable (``ext-table``) directive"""

    option_spec = {
        'name': directives.unchanged
        , 'class': directives.class_option
        , 'header-rows': directives.nonnegative_int
        , 'stub-columns': directives.nonnegative_int
        , 'widths': directives.positive_int_list
        , 'fill-cells' : directives.flag }

    def run(self):

        if not self.content:
            error = self.state_machine.reporter.error(
                'The "%s" directive is empty; content required.' % self.name,
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno)
            return [error]

        title, messages = self.make_title()
        node = nodes.Element()          # anonymous container for parsing
        self.state.nested_parse(self.content, self.content_offset, node)

        tableBuilder = ListTableBuilder(self)
        tableBuilder.parseExtTableNode(node)
        tableNode = tableBuilder.buildTableNode()
        # SDK.CONSOLE()  # print --> tableNode.asdom().toprettyxml()
        if title:
            tableNode.insert(0, title)
        return [tableNode] + messages


# ==============================================================================
class ListTableBuilder(object):
# ==============================================================================

    u"""Builds a table from a double-stage list"""

    def __init__(self, directive):
        self.directive = directive
        self.rows      = []
        self.max_cols  = 0

    def buildTableNode(self):

        colwidths    = self.directive.get_column_widths(self.max_cols)
        if isinstance(colwidths, tuple):
            # Since docutils 0.13, get_column_widths returns a (widths,
            # colwidths) tuple, where widths is a string (i.e. 'auto').
            # See https://sourceforge.net/p/docutils/patches/120/.
            colwidths = colwidths[1]
        stub_columns = self.directive.options.get('stub-columns', 0)
        header_rows  = self.directive.options.get('header-rows', 0)

        table = nodes.table()
        tgroup = nodes.tgroup(cols=len(colwidths))
        table += tgroup
        if 'class' in self.directive.options:
            [table.set_class(c) for c in self.directive.options['class']]

        for colwidth in colwidths:
            colspec = nodes.colspec(colwidth=colwidth)
            # FIXME: It seems, that the stub method only works well in the
            # absence of rowspan (observed by the html builder, the docutils-xml
            # build seems OK).  This is not extraordinary, because there exists
            # no table directive (except *this* ext-table) which allows to
            # define coexistent of rowspan and stubs (there was no use-case
            # before ext-table). This should be reviewed (later).
            if stub_columns:
                colspec.attributes['stub'] = 1
                stub_columns -= 1
            tgroup += colspec
        stub_columns = self.directive.options.get('stub-columns', 0)

        if header_rows:
            thead = nodes.thead()
            tgroup += thead
            for row in self.rows[:header_rows]:
                thead += self.buildTableRowNode(row)

        tbody = nodes.tbody()
        tgroup += tbody

        for row in self.rows[header_rows:]:
            tbody += self.buildTableRowNode(row)
        return table

    def buildTableRowNode(self, row_data, classes=None):
        classes = [] if classes is None else classes
        row = nodes.row()
        for cell in row_data:
            if cell is None:
                continue
            cspan, rspan, cellclasses, cellElements = cell

            attributes = {"classes" : classes}
            if rspan:
                attributes['morerows'] = rspan
            if cspan:
                attributes['morecols'] = cspan
            entry = nodes.entry(**attributes)
            entry.extend(cellElements)
            for cc in cellclasses:
                entry.set_class(cc)
            row += entry
        return row

    def raiseError(self, msg):
        error =  self.directive.state_machine.reporter.error(
            msg
            , nodes.literal_block(self.directive.block_text
                                  , self.directive.block_text)
            , line = self.directive.lineno )
        raise SystemMessagePropagation(error)

    def parseExtTableNode(self, node):
        u"""parses the node from a :py:class:`ExtTable` directive's body"""

        if len(node) != 1 or not isinstance(node[0], nodes.bullet_list):
            self.raiseError(
                'Error parsing content block for the "%s" directive: '
                'exactly one bullet list expected.' % self.directive.name )

        for rowNum, rowItem in enumerate(node[0]):
            row = self.parseRowItem(rowItem, rowNum)
            self.rows.append(row)
        self.roundOffTableDefinition()
        

    def roundOffTableDefinition(self):
        u"""Round off the table definition.
        This method rounds off the table definition in :py:member:`rows`.
        * This method inserts the needed ``None`` values for the missing cells
        arising from spanning cells over rows and/or columns.
        * recount the :py:member:`max_cols`
        * Autospan or fill (option ``fill-cells``) missing cells on the right
          side of the table-row
        """

        y = 0
        while y < len(self.rows):
            x = 0

            while x < len(self.rows[y]):
                cell = self.rows[y][x]
                if cell is None:
                    x += 1
                    continue
                cspan, rspan = cell[:2]
                # handle colspan in current row
                for c in range(cspan):
                    try:
                        self.rows[y].insert(x+c+1, None)
                    except: # pylint: disable=W0702
                        # the user sets ambiguous rowspans
                        pass # SDK.CONSOLE()
                # handle colspan in spanned rows
                for r in range(rspan):
                    for c in range(cspan + 1):
                        try:
                            self.rows[y+r+1].insert(x+c, None)
                        except: # pylint: disable=W0702
                            # the user sets ambiguous rowspans
                            pass # SDK.CONSOLE()
                x += 1
            y += 1

        # Insert the missing cells on the right side. For this, first
        # re-calculate the max columns.

        for row in self.rows:
            if self.max_cols < len(row):
                self.max_cols = len(row)

        # fill with empty cells or cellspan?

        fill_cells = False
        if 'fill-cells' in self.directive.options:
            fill_cells = True

        for row in self.rows:
            x =  self.max_cols - len(row)
            if x and not fill_cells:
                if row[-1] is None:
                    row.append( ( x - 1, 0, [], []) )
                else:
                    cspan, rspan, cellclasses, content = row[-1]
                    row[-1] = (cspan + x, rspan, cellclasses, content)
            elif x and fill_cells:
                for i in range(x):
                    row.append( (0, 0, [], nodes.comment()) )

    def pprint(self):
        # for debugging
        retVal = "[   "
        for row in self.rows:
            retVal += "[ "
            for col in row:
                if col is None:
                    retVal += ('%r' % col)
                    retVal += "\n    , "
                else:
                    content = col[2][0].astext()
                    if len (content) > 30:
                        content = content[:30] + "..."
                    retVal += ('(cspan=%s, rspan=%s, %r)'
                               % (col[0], col[1], content))
                    retVal += "]\n    , "
            retVal = retVal[:-2]
            retVal += "]\n  , "
        retVal = retVal[:-2]
        return retVal + "]"

    def parseRowItem(self, rowItem, rowNum):
        row = []
        childNo = 0
        error   = False
        cell    = None
        target  = None

        for child in rowItem:
            if (isinstance(child , nodes.comment)
                or isinstance(child, nodes.system_message)):
                pass
            elif isinstance(child , nodes.target):
                target = child
            elif isinstance(child, nodes.bullet_list):
                childNo += 1
                cell = child
            else:
                error = True
                break

        if childNo != 1 or error:
            self.raiseError(
                'Error parsing content block for the "%s" directive: '
                'two-level bullet list expected, but row %s does not '
                'contain a second-level bullet list.'
                % (self.directive.name, rowNum + 1))

        for cellItem in cell:
            cspan, rspan, cellclasses, cellElements = self.parseCellItem(cellItem)
            if target is not None:
                cellElements.insert(0, target)
            row.append( (cspan, rspan, cellclasses, cellElements) )
        return row

    def parseCellItem(self, cellItem):
        # search and remove cspan, rspan colspec from the first element in
        # this listItem (field).
        cspan = rspan = 0
        cellclasses = []
        if not len(cellItem):
            return cspan, rspan, [], []
        for elem in cellItem[0]:
            if isinstance(elem, colSpan):
                cspan = elem.get("span")
                elem.parent.remove(elem)
                continue
            if isinstance(elem, rowSpan):
                rspan = elem.get("span")
                elem.parent.remove(elem)
                continue
            if isinstance(elem, cellClass):
                cellclasses = elem.get("classes")
                elem.parent.remove(elem)
                continue
        return cspan, rspan, cellclasses, cellItem[:]