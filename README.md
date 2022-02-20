# Sphinx etx-table directive

Extended list-table directive based on the linuxdoc flat-table.
Features:
 - merged columns
 - merged rows
 - table classes
 - cell classes

The implementation is based on the flat-table directive by Markus Heiser,
part of the linux kernel documentation extensions
(https://github.com/torvalds/linux/blob/master/Documentation/sphinx/rstFlatTable.py).

# Using the extension

Currently the easiest is to copy the directive source into your
repository, add the folder to the python path and add the extension
to the extension list - PIP install is coming.

In `conf.py` add e.g.:

    import os
    import sys
    sys.path.insert(0, os.path.abspath('./exttable'))

    # ...

    extensions = [
        'rstExtTable',
    ]
  
# Example

    .. ext-table:: Some hardware register
      :header-rows: 2
      :class: my-class my-other-class
      :name: my-name

      * - :cspan:`5` :cclass:`header-class` head
      * - len
        - 31:27
        - :cspan:`3` number of valid bits in the data field
      * - data
        - 26:0
        - :cspan:`3` data to transmit LSB first
      * - :rspan:`3` field
        - :rspan:`3` 1:0
        - :cspan:`3` **Controls the bazzle of the braz**

          This field is totally invented for show. We want this line to shop up
          after a linebreak to mimic the normal register descriptions that we
          are used to
      * - AB
        - 0b00
        - do the ab
      * - BC
        - 0b01
        - do the bc
      * - DC
        - 0b10
        - some other meaning



# Developer reference

* http://code.nabla.net/doc/docutils/api/docutils/docutils.nodes.html
* https://docutils.sourceforge.io/docs/howto/rst-directives.html
