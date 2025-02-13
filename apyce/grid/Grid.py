from apyce.utils import misc, Errors
from apyce.io import VTK

import numpy as np

import re


class Grid:
    r"""
    Grid class used in APyCE.

    Attributes
    ----------
    Let G represent a grid in an unstructured format.

    G._filename : string
        A string that holds the name (path) of the grid file.
    G._vtk_unstructured_grid : vtkUnstructuredGrid object
        Object of the VTK library that will be used to store corner-point grid properties and export them to ParaView.
    G._keywords : list
        A list of strings that represents the recognized keywords found in the grid file.
    G._unrec : list
        A list of strings that represents the unrecognized keywords found in the grid file.
    G._n_collapsed : int
        The number of collapsed pillars in the grid.
    G._cart_dims : ndarray
        The dimension of the grid.
    G._num_cell : int
        Number of cells in the global grid.
    G._coord : ndarray
        A list of floating point numbers that represents the COORD keyword from Schlumberger Eclipse.
    G._zcorn : ndarray
        A list of floating point numbers that represents the ZCORN keyword from Schlumberger Eclipse.
    G._actnum : ndarray
        A list of integer (0 or 1) numbers that represents the ACTNUM keyword from Schlumberger Eclipse.
    G._poro : ndarray
        A list of floating point numbers that represents the PORO keyword from Schlumberger Eclipse.
    G._permx : ndarray
        A list of floating point numbers that represents the PERMX keyword from Schlumberger Eclipse.
    G._permy : ndarray
        A list of floating point numbers that represents the PERMY keyword from Schlumberger Eclipse.
    G._permz : ndarray
        A list of floating point numbers that represents the PERMZ keyword from Schlumberger Eclipse.
    G._so : ndarray
        A list of floating point numbers that represents the SO keyword from Schlumberger Eclipse.
    G._grid_type : string
        A string that holds the grid type (corner-point / cartesian).
    G._grid_origin : string
        A string that holds the origin of grid file (eclipse / builder).
    G._verbose = boolean
        A boolean that will be used to emit (or not) messages to screen while processing.
    G._dx : ndarray
        A list of floating point numbers that represents the DX keyword from Schlumberger Eclipse.
    G._dy : ndarray
        A list of floating point numbers that represents the DY keyword from Schlumberger Eclipse.
    G._dz : ndarray
        A list of floating point numbers that represents the DZ keyword from Schlumberger Eclipse.
    G._tops : ndarray
        A list of floating point numbers that represents the TOPS keyword from Schlumberger Eclipse.

    Parameters
    ----------
    filename : string, default is 'data.grdecl'.
        A string that holds the name (path) of the grid file.
    grid_origin : string, default is 'eclipse'.
        A string that holds the grid origin (eclipse / builder).
    verbose : boolean, default is True.
        A boolean that will be used to emit (or not) messages to screen while processing.

    Examples
    --------
    >>> import apyce as ap
    >>> G = ap.grid.Grid(filename='dome.grdecl', grid_origin='eclipse', verbose=True)
    >>> G.process_grid()
    >>> G.load_cell_data(filename='dome_Temperature.txt', name='TEMP')
    >>> G.export_data()
    >>> G.plot_grid(filename='Results/dome.vtu', property='TEMP')

    """

    def __init__(self, filename='data.txt', grid_origin='eclipse', verbose=True):
        self._filename = filename

        self._vtk_unstructured_grid = VTK()

        self._keywords = []
        self._unrec = []
        self._n_collapsed = 0

        self._cart_dims = []
        self._num_cell = 0
        self._coord = []
        self._zcorn = []
        self._tops = []
        self._dx = []
        self._dy = []
        self._dz = []
        self._actnum = []
        self._poro = []
        self._permx = []
        self._permy = []
        self._permz = []
        self._so = []

        self._grid_type = ''
        self._grid_origin = grid_origin
        self._verbose = verbose

        if self._grid_origin == 'eclipse':
            self._read_grdecl(self._filename, self._verbose)
        else:
            pass

    def __str__(self):
        header = "-" * 78
        lines = [header, "{0:<35s} {1}".format('keywords', 'value'), header,
                 "{0:<35s} {1}".format('cart_dims', self._cart_dims), "{0:<35s} {1}".format('num_cell', self._num_cell),
                 "{0:<35s} {1}".format('keywords', self._keywords), "{0:<35s} {1}".format('unrec', self._unrec), header]
        return "\n".join(lines)

    def _read_grdecl(self, filename, verbose):
        r"""
        Read subset of ECLIPSE grid file.

        The currently recognized keywords of ECLIPSE are:
            'COORD', 'SPECGRID', 'DIMENS', 'DX', 'DY', 'DZ',
            'TOPS', 'INCLUDE', 'PERMX', 'PERMY', 'PERMZ',
            'PORO', 'ZCORN', 'SO', and 'ACTNUM'.

        Parameters
        ----------
        filename : string
            A string that holds the name (path) of the grid file.
        verbose : boolean
            A boolean that will be used to emit (or not) messages to screen while processing.

        """

        # Check if file exists and can be open
        misc.file_open_exception(filename)

        if verbose:
            print("[INPUT] Reading input ECLIPSE file\n")

        with open(misc.get_path(filename)) as f:
            for line in f:
                # Keyword pattern
                kw = re.match('^[A-Z][A-Z0-9]{0,7}', str(line))

                if kw is not None:
                    if kw.group() == 'SPECGRID':
                        self._grid_type = 'corner-point'
                        if verbose:
                            print("[+] Reading keyword SPECGRID")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        else:
                            raise RuntimeError(Errors.Errors.CART_DIMS_ERROR.value)
                        line = f.readline().strip()
                        self._cart_dims = np.array(re.findall('\d+', str(line))[0:3], dtype=int)
                        self._num_cell = np.prod(self._cart_dims)
                    elif kw.group() == 'DIMENS':
                        self._grid_type = 'cartesian'
                        if verbose:
                            print("[+] Reading keyword DIMENS")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        else:
                            raise RuntimeError(Errors.Errors.CART_DIMS_ERROR.value)
                        line = f.readline().strip()
                        self._cart_dims = np.array(re.findall('\d+', str(line))[0:3], dtype=int)
                        self._num_cell = np.prod(self._cart_dims)
                    elif kw.group() == 'INCLUDE':
                        if verbose:
                            print("[+] Reading keyword INCLUDE")
                        line = f.readline()
                        inc_fn = misc.get_include_file(filename, line)
                        if verbose:
                            print("\t--> {}".format(misc.get_basename(inc_fn)))
                        self._read_grdecl(inc_fn, False)
                        if verbose:
                            print("\t<-- {}".format(misc.get_basename(inc_fn)))
                    elif kw.group() == 'COORD':
                        # Check if grid is already defined
                        misc.check_dim(self._cart_dims, self._num_cell, kw.group(), f)
                        if verbose:
                            print("[+] Reading keyword COORD")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        self._coord = self._read_section_grdecl(f)
                        # Check if self._coord have the correct number of values
                        if len(self._coord) != 6*(self._cart_dims[0]+1)*(self._cart_dims[1]+1):
                            raise ValueError(Errors.Errors.COORD_ERROR.value)
                        self._coord = np.array(self._coord, dtype=float)
                    elif kw.group() == 'ZCORN':
                        # Check if grid is already defined
                        misc.check_dim(self._cart_dims, self._num_cell, kw.group(), f)
                        if verbose:
                            print("[+] Reading keyword ZCORN")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        self._zcorn = self._read_section_grdecl(f)
                        # Check if self._zcorn have the correct number of values
                        if len(self._zcorn) != 8*self._num_cell:
                            raise ValueError(Errors.Errors.ZCORN_ERROR.value)
                        self._zcorn = np.array(self._zcorn, dtype=float)
                    elif kw.group() == 'PORO':
                        # Check if grid is already defined
                        misc.check_dim(self._cart_dims, self._num_cell, kw.group(), f)
                        if verbose:
                            print("[+] Reading keyword PORO")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        self._poro = self._read_section_grdecl(f)
                        # Check if self._poro have the correct number os values
                        if len(self._poro) != self._num_cell:
                            raise ValueError(Errors.Errors.PORO_ERROR.value)
                        self._poro = np.array(self._poro, dtype=float)
                    elif kw.group() == 'PERMX':
                        # Check if grid is already defined
                        misc.check_dim(self._cart_dims, self._num_cell, kw.group(), f)
                        if verbose:
                            print("[+] Reading keyword PERMX")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        self._permx = self._read_section_grdecl(f)
                        # Check if self._permx have the correct number of values
                        if len(self._permx) != self._num_cell:
                            raise ValueError(Errors.Errors.PERMX_ERROR.value)
                        self._permx = np.array(self._permx, dtype=float)
                    elif kw.group() == 'PERMY':
                        # Check if grid is already defined
                        misc.check_dim(self._cart_dims, self._num_cell, kw.group(), f)
                        if verbose:
                            print("[+] Reading keyword PERMY")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        self._permy = self._read_section_grdecl(f)
                        # Check if self._permy have the correct number of values
                        if len(self._permy) != self._num_cell:
                            raise ValueError(Errors.Errors.PERMY_ERROR.value)
                        self._permy = np.array(self._permy, dtype=float)
                    elif kw.group() == 'PERMZ':
                        # Check if grid is already defined
                        misc.check_dim(self._cart_dims, self._num_cell, kw.group(), f)
                        if verbose:
                            print("[+] Reading keyword PERMZ")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        self._permz = self._read_section_grdecl(f)
                        # Check if self._permz have the correct number of values
                        if len(self._permz) != self._num_cell:
                            raise ValueError(Errors.Errors.PERMZ_ERROR.value)
                        self._permz = np.array(self._permz, dtype=float)
                    elif kw.group() == 'ACTNUM':
                        # Check if grid is already defined
                        misc.check_dim(self._cart_dims, self._num_cell, kw.group(), f)
                        if verbose:
                            print("[+] Reading keyword ACTNUM")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        self._actnum = self._read_section_grdecl(f)
                        # Check if self._actnum have the correct number of values
                        if len(self._actnum) != self._num_cell:
                            raise ValueError(Errors.Errors.ACTNUM_ERROR.value)
                        self._actnum = np.array(self._actnum, dtype=int)
                    elif kw.group() == 'SO':
                        # Check if grid is already defined
                        misc.check_dim(self._cart_dims, self._num_cell, kw.group(), f)
                        if verbose:
                            print("[+] Reading keyword SO")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        self._so = self._read_section_grdecl(f)
                        # Check if self._so have the correct number of values
                        if len(self._so) != self._num_cell:
                            raise ValueError(Errors.Errors.SO_ERROR.value)
                        self._so = np.array(self._so, dtype=float)
                    elif kw.group() == 'TOPS':
                        # Check if grid is already defined
                        misc.check_dim(self._cart_dims, self._num_cell, kw.group(), f)
                        if verbose:
                            print("[+] Reading keyword TOPS")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        self._tops = self._read_section_grdecl(f)
                        # Check if self._tops have the correct number of values
                        if len(self._tops) != self._cart_dims[0]*self._cart_dims[1]:
                            raise ValueError(Errors.Errors.TOPS_ERROR.value)
                        self._tops = np.array(self._tops, dtype=float)
                    elif kw.group() == 'DX':
                        # Check if grid is already defined
                        misc.check_dim(self._cart_dims, self._num_cell, kw.group(), f)
                        if verbose:
                            print("[+] Reading keyword DX")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        self._dx = self._read_section_grdecl(f)
                        # Check if self._tops have the correct number of values
                        if len(self._dx) != self._num_cell:
                            raise ValueError(Errors.Errors.DX_ERROR.value)
                        self._dx = np.array(self._dx, dtype=float)
                    elif kw.group() == 'DY':
                        # Check if grid is already defined
                        misc.check_dim(self._cart_dims, self._num_cell, kw.group(), f)
                        if verbose:
                            print("[+] Reading keyword DY")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        self._dy = self._read_section_grdecl(f)
                        # Check if self._tops have the correct number of values
                        if len(self._dy) != self._num_cell:
                            raise ValueError(Errors.Errors.DY_ERROR.value)
                        self._dy = np.array(self._dy, dtype=float)
                    elif kw.group() == 'DZ':
                        # Check if grid is already defined
                        misc.check_dim(self._cart_dims, self._num_cell, kw.group(), f)
                        if verbose:
                            print("[+] Reading keyword DZ")
                        if kw.group() not in self._keywords:
                            self._keywords.append(kw.group())
                        self._dz = self._read_section_grdecl(f)
                        # Check if self._tops have the correct number of values
                        if len(self._dz) != self._num_cell:
                            raise ValueError(Errors.Errors.DZ_ERROR.value)
                        self._dz = np.array(self._dz, dtype=float)
                    elif kw.group() not in self._unrec:
                        if verbose:
                            print("[+] Unrecognized keyword found {}".format(kw.group()))
                        self._unrec.append(kw.group())

    def process_grid(self):
        r"""
        Compute grid topology and geometry from grid description.

        """

        # Check if grid is already defined
        if self._grid_type == 'corner-point':
            misc.check_corner_point_grid(self._cart_dims, self._coord, self._zcorn)
        else:
            misc.check_cartesian_grid(self._cart_dims, self._dx, self._dy, self._dz, self._tops)

        if self._grid_type == 'corner-point':
            if self._grid_origin == 'eclipse':
                self._process_grdecl_corner_point()
            else:
                pass
        else:
            if self._grid_origin == 'eclipse':
                self._process_grdecl_block_centred()
            else:
                pass

    def load_cell_data(self, filename, name):
        r"""
        Read a file with data and append this data to model.

        Parameters
        ----------
        filename : string
            A string that holds the name (path) of the grid file.
        name : string
            A string that holds the name of the property.

        Notes
        -----
        Assuming that the data to be loaded is a reservoir
            property that has a value for each cell, we must have NX * NY * NZ values

        The file must not contain the keyword.

        Examples
        --------
        1 0 1 0 1 0 1 1 0 1
        1 0 0 0 0 0 0 0 0 1
        ...
        1 0 1 0 0 1 0 0 1 0

        Do not use

        ACTNUM
        1 0 1 0 1 0 1 1 0 1
        1 0 0 0 0 0 0 0 0 1
        ...
        1 0 1 0 0 1 0 0 1 0

        """

        # Check if file exists and can be open
        misc.file_open_exception(filename)

        # Check if grid is already defined
        if self._grid_type == 'corner-point':
            misc.check_corner_point_grid(self._cart_dims, self._coord, self._zcorn)
        else:
            misc.check_cartesian_grid(self._cart_dims, self._dx, self._dy, self._dz, self._tops)

        with open(misc.get_path(filename)) as f:
            if self._verbose:
                print("[+] Reading keyword {}".format(name))
            data_array = self._read_section_grdecl(f)
            if name not in self._keywords:
                self._keywords.append(name)
            if len(data_array) != self._num_cell:
                raise ValueError(Errors.Errors.LOAD_CELL_DATA_ERROR.value.replace('{}', name))
            data_array = np.array(data_array, dtype=float)

        self._update(data_array, name)

    def plot_grid(self, filename='Data/Results/dome.vtu', lighting=False, property='PORO', show_edges=True, specular=0.0,
                  specular_power=0.0, show_scalar_bar=True, cmap='viridis'):
        r"""
        Plot the grid with PyVista.

        Parameters
        ----------
        filename : string, default is 'Data/Results/dome.vtu'
            String holding the path to VTU file.
        lighting : boolean, default is False
            Enable or disable view direction lighting.
        property : string, default is 'PORO'
            String holding the name of property that will be plotted.
        show_edges : boolean, default is True
            Shows the edges of a mesh.  Does not apply to a wireframe representation.
        specular : float, default is 0.0
            The specular lighting coefficient.
        specular_power : float, default is 0.0
            The specular power. Between 0.0 and 128.0.
        show_scalar_bar : boolean, default is True
            If False, a scalar bar will not be added to the scene.
        cmap : string, default is 'viridis'
            Name of the Matplotlib colormap to us when mapping the 'scalars'. See available Matplotlib colormaps.

        Notes
        -----
        https://www.pyvista.org/

        """

        import matplotlib.pyplot as plt
        import pyvista as pv

        # Check if file exists and can be open
        misc.file_open_exception(filename)

        # Check if grid is already defined
        if self._grid_type == 'corner-point':
            misc.check_corner_point_grid(self._cart_dims, self._coord, self._zcorn)
        else:
            misc.check_cartesian_grid(self._cart_dims, self._dx, self._dy, self._dz, self._tops)

        # Set theme
        pv.set_plot_theme("document")

        # Color map
        cmap = plt.cm.get_cmap(cmap, 5)

        # Mesh to be plotted
        mesh = pv.UnstructuredGrid(misc.get_path(filename))

        # Remove ghost cells if they are present in the mesh
        if 'ACTNUM' in mesh.array_names:
            ghosts = np.argwhere(mesh["ACTNUM"] < 1)
            mesh.remove_cells(ghosts)

        # Plot the grid
        mesh.plot(lighting=lighting, specular=specular, specular_power=specular_power, show_edges=show_edges,
                   scalars=property, show_scalar_bar=show_scalar_bar, cmap=cmap)

    def export_data(self):
        r"""
        Save grid data to a single vtu file for visualizing in ParaView.

        Notes
        -----
        The vtu file will be created on the directory 'Results' that will be created
            on the same directory than grid file

        """

        VTK.export_data(self._filename, self._vtk_unstructured_grid, self._verbose)

    def _read_section_grdecl(self, file):
        r"""
        Read the section of data in the ECLIPSE input file
        and return the array of values.

        Parameters
        ----------
        file : file object
            File object that have the ECLIPSE grid specification.

        """

        section = []
        while True:
            line = file.readline()
            if line.startswith('--') or not line.strip():
                # Ignore blank lines and comments
                continue
            values = misc.expand_scalars(line)
            section.extend(values)
            if section[-1] == '/':
                section.pop()
                break
        return section

    def _process_grdecl_corner_point(self):
        r"""
        Compute grid topology and geometry from ECLIPSE pillar grid description.

        Notes
        -----
        The VTK Hexahedron indexes elements differently than ECLIPSE.

        Therefore, we must convert indexes from ECLIPSE to VTK Hexahedron before creating the cells.

        ECLIPSE:
           6 --------- 7
          /|          /|
         / |         / |
        4 --------- 5  |
        |  |        |  |
        |  2 -------|- 3
        | /         | /
        |/          |/
        0 --------- 1

        VTK Hexahedron:
           7 --------- 6
          /|          /|
         / |         / |
        4 --------- 5  |
        |  |        |  |
        |  3 -------|- 2
        | /         | /
        |/          |/
        0 --------- 1

        As we can see, the VTK Hexahedron indexes 2, 3, 6, and 7 are different from Eclipse.

        See also
        --------
        https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf (page 9 - VTK_HEXAHEDRON)

        """

        if self._verbose:
            print("\n[PROCESS] Converting GRDECL corner-point grid to ParaView VTU format")

        points = VTK.create_points()
        points.SetNumberOfPoints(8*np.prod(self._cart_dims))  # 2*NX*2*NY*2*NZ

        # Recover logical dimension of grid
        nx, ny, nz = self._cart_dims[0:3]

        if self._verbose:
            print("\n[+] Creating VTK Points")

        point_id = 0
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    # Get the cell coords
                    coords = self._get_cell_coords(i, j, k)
                    # Set the points for the cell
                    for pi in range(8):
                        points.SetPoint(point_id, coords[pi])
                        point_id += 1
        self._vtk_unstructured_grid.SetPoints(points)

        if self._verbose:
            print("\n\t[+] Created {} VTK Points".format(self._vtk_unstructured_grid.GetNumberOfPoints()))

            print("\t[+] Detected {} collapsed pillars.".format(self._n_collapsed))

            if "ACTNUM" in self._keywords:
                _active_cells = [x for x in self._actnum if x == 1]
                _inactive_cells = len(self._actnum) - len(_active_cells)
                print("\t[+] Detected {} active cells and {} inactive cells.".format(len(_active_cells), _inactive_cells))

            print("\n[+] Creating VTK Cells")

        # Removes inactive cells (ACTNUM = 0)
        if len(self._actnum) != 0:
            self._remove_cells()

        cell_id = 0
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    cell = VTK.create_hexahedron()

                    cell.GetPointIds().SetId(0, cell_id*8+0)
                    cell.GetPointIds().SetId(1, cell_id*8+1)
                    cell.GetPointIds().SetId(2, cell_id*8+3)
                    cell.GetPointIds().SetId(3, cell_id*8+2)
                    cell.GetPointIds().SetId(4, cell_id*8+4)
                    cell.GetPointIds().SetId(5, cell_id*8+5)
                    cell.GetPointIds().SetId(6, cell_id*8+7)
                    cell.GetPointIds().SetId(7, cell_id*8+6)

                    self._vtk_unstructured_grid.InsertNextCell(cell.GetCellType(), cell.GetPointIds())

                    cell_id += 1

        if self._verbose:
            print("\n\t[+] Created {} VTK Cells".format(self._vtk_unstructured_grid.GetNumberOfCells()))

        # Set the properties to the vtk array
        self._update()

    def _process_grdecl_block_centred(self):
        r"""
        Compute grid topology and geometry from ECLIPSE cartesian (block-centred) grid description.

        ECLIPSE Grid block

                +-----------> I
               /|
              / |     0 --------- 1
             /  |    /|          /|
          J v   |   / |         / |
                |  2 --------- 3  |
              K v  |  |        |  |
                   |  4 -------|- 5
                   | /         | /
                   |/          |/
                   6 --------- 7


            For a 9 x 3 x 1 grid

            I Pairs

            +-----------> I
            |   0---(1,2)---(3,4)---(5,6)---(7,8)---(9,10)---(11,12)---(13,14)---(15,16)---17
            |   |
            |   |
            v   |
            J   0---(1,2)---(3,4)---(5,6)---(7,8)---(9,10)---(11,12)---(13,14)---(15,16)---17
                |
                |
                |
                ()----

                Cell 0 and Cell 1 in terms of i
                0---1---3
                |   |   |
                |   |   |
                0---1---3

                spliting

                0---1 2---3
                |   | |   |
                |   | |   |
                0---1 2---3

            J Pairs

            +-----------> I
            |   0---0---0---0---0---0---0---0---0---0
            |   |
            |   |
            v   |
            J   (1,2)---(1,2)---(1,2)---(1,2)---(1,2)---(1,2)---(1,2)---(1,2)---(1,2)---(1,2)
                |
                |
                |
                (3,4)---(3,4)---(3,4)---(3,4)---(3,4)---(3,4)---(3,4)---(3,4)---(3,4)---(3,4)
                |
                |
                |
                5---5---5---5---5---5---5---5---5---5


                  +-----------> I
                 /|
                / |     0 --------- a --------- b     a = (1,2)
               /  |    /|          /|          /|     b = (3,4)
            J v   |   / |         / |         / |     ...
                  |  x --------- x --------- x  |     some points are shared between cells
                K v  |  |        |  |        |  |
                     |  x -------|- x -------|- x
                     | /         | /         | /
                     |/          |/          |/
                     x --------- x --------- x

        """

        if self._verbose:
            print("\n[PROCESS] Converting GRDECL cartesian grid to VTU")

        # recover grid dimensions
        dx, dy, dz, tops = self._dx, self._dy, self._dz, self._tops
        nx, ny, nz = self._cart_dims[0:3]

        # creates coordinate arrays
        coord_x = np.zeros((2*nx, 2*ny, 2*nz))
        coord_y = np.zeros((2*nx, 2*ny, 2*nz))
        coord_z = np.zeros((2*nx, 2*ny, 2*nz))

        for k in range(2*nz):
            for j in range(2*ny):
                for i in range(2*nx):

                    I, J, K = int(i/2), int(j/2), int(k/2)

                    ijk = misc.get_ijk(I, J, K, nx, ny, nz)

                    # 0s
                    if i == 0:
                        coord_x[i][i][k] = 0
                    if j == 0:
                        coord_y[i][j][k] = 0
                    if k == 0:
                        coord_z[i][j][k] = tops[ijk]

                    # i, j, k varying
                    if 0 < i < 2*nx-1:
                        ijk = misc.get_ijk(I, J, K, nx, ny, nz)
                        coord_x[i][j][k] = dx[ijk]
                        if i > 2:
                            r"""
                            i
                            ------>

                            0---(1,2)---(3,4)---(5,6)---(7,8)---9

                            """
                            # we need to add the value of the last coord to get the spacing between cells
                            coord_x[i][j][k] = dx[ijk] + coord_x[i-1][j][k]
                        if i > 1 and i%2 == 0:
                            # cells that are even have the same coordinate than previous odd cells
                            coord_x[i][j][k] = coord_x[i-1][j][k]
                    if 0 < j < 2*ny-1:
                        ijk = misc.get_ijk(I, J, K, nx, ny, nz)
                        coord_y[i][j][k] = dy[ijk]
                        if j > 2:
                            coord_y[i][j][k] = dy[ijk] + coord_y[i][j-1][k]
                        if j > 1 and j%2 == 0:
                            # cells that are even have the same coordinate than previous odd cells
                            coord_y[i][j][k] = coord_y[i][j-1][k]
                    if 0 < k < 2*nz-1:
                        ijk = misc.get_ijk(I, J, K, nx, ny, nz)
                        coord_z[i][j][k] = dz[ijk]
                        if k > 2:
                            coord_z[i][j][k] = dz[ijk] + coord_z[i][j][k-1]
                        if k > 1 and k%2 == 0:
                            # cells that are even have the same coordinate than previous odd cells
                            coord_z[i][j][k] = coord_z[i][j][k-1]

                    # final points
                    if i == 2*nx-1:
                        ijk = misc.get_ijk(I, J, K, nx, ny, nz)
                        # we need to add the value of the last coord to get the spacing between cells
                        coord_x[i][j][k] = dx[ijk] + coord_x[i-1][j][k]
                    if j == 2*ny-1:
                        ijk = misc.get_ijk(I, J, K, nx, ny, nz)
                        # we need to add the value of the last coord to get the spacing between cells
                        coord_y[i][j][k] = dy[ijk] + coord_y[i][j-1][k]
                    if k == 2*nz-1:
                        ijk = misc.get_ijk(I, J, K, nx, ny, nz)
                        # we need to add the value of the last coord to get the spacing between cells
                        coord_z[i][j][k] = dz[ijk] + coord_z[i][j][k-1]


        points = VTK.create_points()
        points.SetNumberOfPoints(8*np.prod(self._cart_dims))  # 2*NX*2*NY*2*NZ

        if self._verbose:
            print("\n[+] Creating VTK Points")

        point_id = 0
        for k in range(2*nz):
            for j in range(2*ny):
                for i in range(2*nx):
                    # Set the points for the cell
                    points.SetPoint(point_id, [coord_x[i][j][k],coord_y[i][j][k],coord_z[i][j][k]])
                    point_id += 1

        self._vtk_unstructured_grid.SetPoints(points)

        if self._verbose:
            print("\n\t[+] Created {} VTK Points".format(self._vtk_unstructured_grid.GetNumberOfPoints()))

            print("\n[+] Creating VTK Cells")

        cell_id = 0
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    cell = VTK.create_hexahedron()

                    # k = 0
                    cell.GetPointIds().SetId(0, misc.get_ijk(2*i, 2*j, 2*k, 2*nx, 2*ny, 2*nz))
                    cell.GetPointIds().SetId(1, misc.get_ijk(2*i+1, 2*j, 2*k, 2*nx, 2*ny, 2*nz))
                    cell.GetPointIds().SetId(3, misc.get_ijk(2*i, 2*j+1, 2*k, 2*nx, 2*ny, 2*nz)) # swap 2 and 3 (eclipse -> vtk)
                    cell.GetPointIds().SetId(2, misc.get_ijk(2*i+1, 2*j+1, 2*k, 2*nx, 2*ny, 2*nz))

                    # k = 1
                    cell.GetPointIds().SetId(4, misc.get_ijk(2*i, 2*j, 2*k+1, 2*nx, 2*ny, 2*nz))
                    cell.GetPointIds().SetId(5, misc.get_ijk(2*i+1, 2*j, 2*k+1, 2*nx, 2*ny, 2*nz))
                    cell.GetPointIds().SetId(7, misc.get_ijk(2*i, 2*j+1, 2*k+1, 2*nx, 2*ny, 2*nz)) # swap 6 and 7 (eclipse -> vtk)
                    cell.GetPointIds().SetId(6, misc.get_ijk(2*i+1, 2*j+1, 2*k+1, 2*nx, 2*ny, 2*nz))

                    self._vtk_unstructured_grid.InsertNextCell(cell.GetCellType(), cell.GetPointIds())
                    cell_id += 1

        if self._verbose:
            print("\n\t[+] Created {} VTK Cells".format(self._vtk_unstructured_grid.GetNumberOfCells()))

        # Set the properties to the vtk array
        self._update()

    def _get_cell_coords(self, i, j, k):
        r"""
        Get XYZ coords for each node of a cell.

        Parameters
        ----------
        i, j, k : int
            Values from grid dimension.

        Notes
        -----
        In corner-point grid, the nodes are ordained like the follow example:

        n6    n7
        x------x
        |      |
        |      | This is the bottom face
        x------x
        n4    n5

        n2    n3
        x------x
        |      |
        |      | This is the top face
        x------x
        n0    n1

           6 --------- 7
          /|  btm     /|
         / |  face   / |
        4 --------- 5  |
        |  |        |  |
        |  2 -------|- 3
        | /   top   | /
        |/    face  |/
        0 --------- 1

        """

        coord = []

        # Get pillars for this cell
        pillars = self._get_pillars(i, j)

        # Get the Zs for this cell (The depth of the nodes)
        zs = self._get_zs(i, j, k)

        # Loop eight times for each cell (eight corners)
        for pi in range(8):
            r"""
            Recover physical nodal coordinates along pillars.

            We assume that all pillars are straight lines so linear interpolation is sufficient.
            As a special case we need to handle "collapsed" pillars of the form

            x0 y0 z0   x0 y0 z0

            where the top pillar point coincides with the bottom pillar point. (degenerated cell)
            Following ECLIPSE, we assume that such pillars are really vertical...

            In MRST:
            ix    = abs(lines(:,6) - lines(:,3)) < abs(opt.CoincidenceTolerance);
            t     = (grdecl.ZCORN(:) - lines(:,3)) ./ (lines(:,6) - lines(:,3));
            t(ix) = 0;

            xCoords = lines(:,1) + t.*(lines(:,4) - lines(:,1));
            yCoords = lines(:,2) + t.*(lines(:,5) - lines(:,2));

            In APyCE:
            MRST performs this process only once, this is because the array [lines]
            already contain all the necessary coordinates, here in APyCE,
            we will do the process cell by cell.

            """

            # p_idx -> [0,3]
            p_idx = pi % 4

            # Absolute tolerance used to detect collapsed pillars where the top
            # pillar point coincides with the bottom pillar point
            coincidence_tolerance = 2.2204e-14

            pillar = pillars[p_idx]
            z_coord = zs[pi]

            # degenerated cell condition
            if abs(pillar[1][2] - pillar[0][2]) < coincidence_tolerance:
                self._n_collapsed += 1
                t = 0.0
            else:
                t = (z_coord - pillar[0][2]) / (pillar[1][2] - pillar[0][2])

            x_coord = pillar[0][0] + t * (pillar[1][0] - pillar[0][0])
            y_coord = pillar[0][1] + t * (pillar[1][1] - pillar[0][1])

            coord.append(np.array([x_coord, y_coord, z_coord]))

        return coord

    def _get_pillars(self, i, j):
        r"""
        Obtain the pillars index in [COORD] and the pillars coord for each cell.

        Parameters
        ----------
        i, j : int
            Values from grid dimension.

        In Corner-Point grid, the pillars are ordained like the follow example:

        p2    p3
        x------x
        |      |
        |      |
        x------x
        p0    p1

        In a 2D system (2x2x1), we have:

        6 --- 7 --- 8
        |  2  |  3  |
        3 --- 4 --- 5
        |  0  |  1  |
        0 --- 1 --- 2

        As you can see:

        (0,1,3,4) - cell 0
        (1,2,4,5) - cell 1
        (3,4,6,7) - cell 2
        (4,5,7,8) - cell 3

        Some pillars are shared between cells

        """

        pillars = []

        # Recover logical dimension of grid
        # There are (nx+1)*(ny+1) pillars lines
        nx, ny = self._cart_dims[0]+1, self._cart_dims[1]+1

        # Get the pillar index in [COORD]
        p0 = misc.get_ijk(i, j, 0, nx, ny, 0)
        p1 = misc.get_ijk(i+1, j, 0, nx, ny, 0)
        p2 = misc.get_ijk(i, j+1, 0, nx, ny, 0)
        p3 = misc.get_ijk(i+1, j+1, 0, nx, ny, 0)

        r"""
        In ECLIPSE, the [COORD] keyword follow the pattern below:
        1. A coordinate line (pillar) is specified by two triplets of
            X, Y, and Z coordinates, representing two distinct points on it

        So, we have:
            COORD
            xtop ytop ztop xbtm ybtm zbtm
            xtop ytop ztop xbtm ybtm zbtm
            xtop ytop ztop xbtm ybtm zbtm
            .
            .
            .
            xtop ytop ztop xbtm ybtm zbtm

        """

        # Get the pillar from [COORD]
        # Create an array with the four pillars' index
        pillars_idx = [p0, p1, p2, p3]

        for pillar_idx in pillars_idx:
            top_idx = [6*pillar_idx, 6*pillar_idx+1, 6*pillar_idx+2]
            btm_idx = [6*pillar_idx+3, 6*pillar_idx+4, 6*pillar_idx+5]

            top_points = np.array([self._coord[x] for x in top_idx])
            btm_points = np.array([self._coord[x] for x in btm_idx])

            pillars.append([top_points, btm_points])

        return pillars

    def _get_zs(self, i, j, k):
        r"""
        Get the Z index in [ZCORN] and Z coords for a cell, each cell have eight Zs (depth of nodes).

        Parameters
        ----------
        i, j, k : int
            Values from grid dimension.

        The depths of the corner points of each cell are specified with 2*NX * 2*NY * 2*NZ values.
            First the two corners in the i-direction of the first grid cell is given,
            then the two corner of the next grid block in the i-direction etc.
            The unit of the values is metres, and the depth values are positive with increasing values downwards.

        """

        # Recover logical dimension of grid (*2 because we have 8*nx*ny*nz values from [ZCORN])
        nx, ny, nz = 2 * self._cart_dims[0], 2 * self._cart_dims[1], 2 * self._cart_dims[2]

        # Zs from top layer
        z0 = misc.get_ijk(2*i, 2*j, 2*k, nx, ny, nz)
        z1 = misc.get_ijk(2*i+1, 2*j, 2*k, nx, ny, nz)
        z2 = misc.get_ijk(2*i, 2*j+1, 2*k, nx, ny, nz)
        z3 = misc.get_ijk(2*i+1, 2*j+1, 2*k, nx, ny, nz)

        # Zs from bottom layer
        z4 = misc.get_ijk(2*i, 2*j, 2*k+1, nx, ny, nz)
        z5 = misc.get_ijk(2*i+1, 2*j, 2*k+1, nx, ny, nz)
        z6 = misc.get_ijk(2*i, 2*j+1, 2*k+1, nx, ny, nz)
        z7 = misc.get_ijk(2*i+1, 2*j+1, 2*k+1, nx, ny, nz)

        # Create an array with the eight zs' index
        zs_idx = [z0, z1, z2, z3, z4, z5, z6, z7]

        return [self._zcorn[x] for x in zs_idx]

    def _remove_cells(self):
        r"""
        Remove the inactive cells of the model.

        Only works if exported to ParaView!

        """

        ind = np.argwhere(self._actnum == 0)
        ghost_cells = np.zeros(self._num_cell, np.uint8)
        ghost_cells[ind] = VTK.get_duplicatecell()
        self._vtk_unstructured_grid.AllocateCellGhostArray()
        ghosts = self._vtk_unstructured_grid.GetCellGhostArray()
        for i in ghost_cells:
            ghosts.InsertNextTuple1(i)

    def _update(self, data_array=[], name='PROPERTY'):
        r"""
        This method update the data in the vtkUnsctructuredGrid.

        Parameters
        ----------
        data_array : ndarray
            NumPy array holding the data of load_cell_data().
        name : string
            String holding the name of the property.

        """

        if len(self._actnum) != 0:
            VTK.numpy_to_vtk('ACTNUM', self._actnum, self._vtk_unstructured_grid, self._verbose)
        if len(self._permx) != 0:
             VTK.numpy_to_vtk('PERMX', self._permx, self._vtk_unstructured_grid, self._verbose)
        if len(self._permy) != 0:
            VTK.numpy_to_vtk('PERMY', self._permy, self._vtk_unstructured_grid, self._verbose)
        if len(self._permz) != 0:
            VTK.numpy_to_vtk('PERMZ', self._permz, self._vtk_unstructured_grid, self._verbose)
        if len(self._poro) != 0:
            VTK.numpy_to_vtk('PORO', self._poro, self._vtk_unstructured_grid, self._verbose)
        if len(self._so) != 0:
            VTK.numpy_to_vtk('SO', self._so, self._vtk_unstructured_grid, self._verbose)
        if len(data_array) != 0:
            VTK.numpy_to_vtk(name.upper(), data_array, self._vtk_unstructured_grid, self._verbose)