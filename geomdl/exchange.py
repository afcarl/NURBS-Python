"""
.. module:: exchange
    :platform: Unix, Windows
    :synopsis: CAD exchange and interoperability module for NURBS-Python

.. moduleauthor:: Onur Rauf Bingol <orbingol@gmail.com>

"""

from . import os
from . import warnings
from . import struct
from . import Abstract
from . import NURBS
from . import Multi
from . import compatibility
from .elements import Vertex, Triangle


def read_txt(file_name, two_dimensional=False):
    """ Reads control points from a text file and generates a 1-D list of control points.

    :param file_name: file name of the text file
    :type file_name: str
    :param two_dimensional: type of the text file
    :type two_dimensional: bool
    :return: list of control points, if two_dimensional, then also returns size in u- and v-directions
    :rtype: list
    """
    ctrlpts = []

    # Try opening the file for reading
    try:
        with open(file_name, 'r') as fp:
                if two_dimensional:
                    # Start reading file
                    size_u = 0
                    size_v = 0
                    for line in fp:
                        # Remove whitespace
                        line = line.strip()
                        # Convert the string containing the coordinates into a list
                        control_point_row = line.split(';')
                        # Clean and convert the values
                        size_v = 0
                        for cpr in control_point_row:
                            ctrlpts.append([float(c.strip()) for c in cpr.split(',')])
                            size_v += 1
                        size_u += 1

                    # Return control points, size in u- and v-directions
                    return ctrlpts, size_u, size_v
                else:
                    # Start reading file
                    for line in fp:
                        # Remove whitespace
                        line = line.strip()
                        # Clean and convert the values
                        ctrlpts.append([float(c.strip()) for c in line.split(',')])

                    # Return control points
                    return ctrlpts
    except IOError:
        # Show a warning on failure to open file
        warnings.warn("File " + str(file_name) + " cannot be opened for reading")


def export_csv(obj, file_name, point_type='evalpts'):
    """ Exports control points or evaluated points as a CSV file.

    :param obj: a curve or a surface object
    :type obj: Abstract.Curve, Abstract.Surface
    :param file_name: output file name
    :type file_name: str
    :param point_type: ``ctrlpts`` for control points or ``evalpts`` for evaluated points
    :type point_type: str
    """
    if not isinstance(obj, (Abstract.Curve, Abstract.Surface)):
        raise ValueError("Input object should be a curve or a surface")

    # Pick correct points from the object
    if point_type == 'ctrlpts':
        points = obj.ctrlpts
    elif point_type == 'evalpts' or point_type == 'curvepts' or point_type == 'surfpts':
        points = obj.evalpts
    else:
        warnings.warn("Please choose a valid point type option")
        return

    # Prepare CSV header
    dim = len(points[0])
    header = "dim "
    for i in range(dim-1):
        header += str(i + 1) + ", dim "
    header += str(dim) + "\n"

    # Try opening the file for writing
    try:
        with open(file_name, 'w') as fp:
            # Write header to the file
            fp.write(header)

            # Loop through points
            for pt in points:
                # Fill coordinates
                line = ", ".join(str(c) for c in pt) + "\n"
                # Write line to file
                fp.write(line)

    except IOError:
        # Show a warning on failure to open file
        warnings.warn("File " + str(file_name) + " cannot be opened for writing.")


def export_vtk(obj, file_name, point_type='evalpts'):
    """ Exports control points or evaluated points as a VTK file (legacy format).

    Please see the following document for details: http://www.vtk.org/VTK/img/file-formats.pdf

    :param obj: a curve or a surface object
    :type obj: Abstract.Curve, Abstract.Surface
    :param file_name: output file name
    :type file_name: str
    :param point_type: ``ctrlpts`` for control points or ``evalpts`` for evaluated points
    :type point_type: str
    """
    if not isinstance(obj, (Abstract.Curve, Abstract.Surface)):
        raise ValueError("Input object should be a curve or a surface")

    # Pick correct points from the object
    if point_type == 'ctrlpts':
        points = obj.ctrlpts
    elif point_type == 'evalpts' or point_type == 'curvepts' or point_type == 'surfpts':
        points = obj.evalpts
    else:
        warnings.warn("Please choose a valid point type option")
        return

    # Try opening the file for writing
    try:
        with open(file_name, 'w') as fp:
            # Write header to the file
            fp.write("# vtk DataFile Version 3.0\n")
            fp.write(repr(obj) + "\n")
            fp.write("ASCII\nDATASET POLYDATA\n")
            fp.write("POINTS " + str(len(points)) + " FLOAT\n")

            # Loop through points
            for pt in points:
                line = " ".join(str(c) for c in pt) + "\n"
                fp.write(line)

    except IOError:
        # Show a warning on failure to open file
        warnings.warn("File " + str(file_name) + " cannot be opened for writing.")


# Saves surface(s) as a .obj file
def save_obj(surf_in, file_name, **kwargs):
    """ Exports surface(s) as a .obj file.

    :param surf_in: surface or surfaces to be saved
    :type surf_in: Abstract.Surface or Multi.MultiSurface
    :param file_name: name of the output file
    :type file_name: str

    Keyword Arguments:
        * *vertex_spacing* (``int``): size of the triangle edge in terms of points sampled on the surface

    """
    vertex_spacing = kwargs.get('vertex_spacing', 2)

    if isinstance(surf_in, Multi.MultiSurface):
        save_obj_multi(surf_in, file_name=file_name, vertex_spacing=vertex_spacing)
    else:
        save_obj_single(surf_in, file_name=file_name, vertex_spacing=vertex_spacing)


# Saves surface(s) as a .stl file
def save_stl(surf_in, file_name, **kwargs):
    """ Exports surface(s) as a .stl file in plain text or binary format.

    :param surf_in: surface or surfaces to be saved
    :type surf_in: Abstract.Surface or Multi.MultiSurface
    :param file_name: name of the output file
    :type file_name: str

    Keyword Arguments:
        * *binary* (``bool``): True if the saved STL file is going to be in binary format
        * *vertex_spacing* (``int``): size of the triangle edge in terms of points sampled on the surface

    """
    binary = kwargs.get('binary', True)
    vertex_spacing = kwargs.get('vertex_spacing', 2)

    if isinstance(surf_in, Multi.MultiSurface):
        if binary:
            save_stl_binary_multi(surf_in, file_name=file_name, vertex_spacing=vertex_spacing)
        else:
            save_stl_ascii_multi(surf_in, file_name=file_name, vertex_spacing=vertex_spacing)
    else:
        if binary:
            save_stl_binary_single(surf_in, file_name=file_name, vertex_spacing=vertex_spacing)
        else:
            save_stl_ascii_single(surf_in, file_name=file_name, vertex_spacing=vertex_spacing)


# Saves surface(s) as a .off file
def save_off(surf_in, file_name, **kwargs):
    """ Exports surface(s) as a .off file.

    :param surf_in: surface or surfaces to be saved
    :type surf_in: Abstract.Surface or Multi.MultiSurface
    :param file_name: name of the output file
    :type file_name: str

    Keyword Arguments:
        * *vertex_spacing* (``int``): size of the triangle edge in terms of points sampled on the surface

    """
    vertex_spacing = kwargs.get('vertex_spacing', 2)

    if isinstance(surf_in, Multi.MultiSurface):
        save_off_multi(surf_in, file_name=file_name, vertex_spacing=vertex_spacing)
    else:
        save_off_single(surf_in, file_name=file_name, vertex_spacing=vertex_spacing)


# Generates triangles
def _gen_triangles_vertices(points, row_size, col_size, vertex_spacing):
    points2d = []
    for i in range(0, col_size):
        row_list = []
        for j in range(0, row_size):
            row_list.append(points[j + (i * row_size)])
        points2d.append(row_list)

    u_range = 1.0 / float(col_size - 1)
    v_range = 1.0 / float(row_size - 1)
    vertices = []
    vert_id = 1
    u = 0.0
    for col_idx in range(0, col_size, vertex_spacing):
        vert_list = []
        v = 0.0
        for row_idx in range(0, row_size, vertex_spacing):
            temp = Vertex()
            temp.data = points2d[col_idx][row_idx]
            temp.id = vert_id
            temp.uv = [u, v]
            vert_list.append(temp)
            vert_id += 1
            v += v_range
        vertices.append(vert_list)
        u += u_range

    v_col_size = len(vertices)
    v_row_size = len(vert_list)

    tri_id = 1
    forward = True
    triangles = []
    for col_idx in range(0, v_col_size - 1):
        row_idx = 0
        left_half = True
        tri_list = []
        while row_idx < v_row_size - 1:
            tri = Triangle()
            if left_half:
                tri.add_vertex(vertices[col_idx + 1][row_idx])
                tri.add_vertex(vertices[col_idx][row_idx])
                tri.add_vertex(vertices[col_idx][row_idx + 1])
                left_half = False
            else:
                tri.add_vertex(vertices[col_idx][row_idx + 1])
                tri.add_vertex(vertices[col_idx + 1][row_idx + 1])
                tri.add_vertex(vertices[col_idx + 1][row_idx])
                left_half = True
                row_idx += 1
            tri.id = tri_id
            tri_list.append(tri)
            tri_id += 1
        if forward:
            forward = False
        else:
            forward = True
            tri_list.reverse()
        triangles += tri_list

    return vertices, triangles


def save_obj_single(surface, **kwargs):
    """ Saves a single surface as a .obj file.

    :param surface: surface to be saved
    :type surface: Abstract.Surface

    Keyword Arguments:
        * file_name (str): name of the output file
        * vertex_spacing (int): size of the triangle edge in terms of points sampled on the surface

    """
    # Get keyword arguments
    file_name = kwargs.get('file_name', 'default.obj')
    vertex_spacing = kwargs.get('vertex_spacing', 2)

    # Input validity checking
    if not isinstance(surface, Abstract.Surface):
        raise ValueError("Input is not a surface")
    if vertex_spacing < 1 or not isinstance(vertex_spacing, int):
        raise ValueError("Vertex spacing must be an integer value and it must be bigger than zero")

    # Create the file and start saving triangulated surface points
    try:
        with open(file_name, 'w') as fp:
            fp.write("# Generated by NURBS-Python\n")
            vertices, triangles = _gen_triangles_vertices(surface.surfpts,
                                                          surface.sample_size, surface.sample_size,
                                                          vertex_spacing)

            # Write vertices
            for vert_row in vertices:
                for vert in vert_row:
                    line = "v " + str(vert.x) + " " + str(vert.y) + " " + str(vert.z) + "\n"
                    fp.write(line)

            # Write vertex normals
            for vert_row in vertices:
                for vert in vert_row:
                    sn = surface.normal(vert.uv[0], vert.uv[1], True)
                    line = "vn " + str(sn[1][0]) + " " + str(sn[1][1]) + " " + str(sn[1][2]) + "\n"
                    fp.write(line)

            # Write faces
            for t in triangles:
                vl = t.vertex_ids
                line = "f " + str(vl[0]) + " " + str(vl[1]) + " " + str(vl[2]) + "\n"
                fp.write(line)
    except IOError:
        print("Cannot open " + str(file_name) + " for writing")


def save_obj_multi(surface_list, **kwargs):
    """ Saves multiple surfaces as a single .obj file.

    :param surface_list: list of surfaces to be saved
    :type surface_list: Multi.MultiSurface

    Keyword Arguments:
        * file_name (str): name of the output file
        * vertex_spacing (int): size of the triangle edge in terms of points sampled on the surface

    """
    # Get keyword arguments
    file_name = kwargs.get('file_name', 'default.obj')
    vertex_spacing = kwargs.get('vertex_spacing', 2)

    # Input validity checking
    if not isinstance(surface_list, Multi.MultiSurface):
        raise ValueError("Input must be a list of surfaces")
    if vertex_spacing < 1 or not isinstance(vertex_spacing, int):
        raise ValueError("Vertex spacing must be an integer value and it must be bigger than zero")

    # Create the file and start saving triangulated surface points
    try:
        with open(file_name, 'w') as fp:
            fp.write("# Generated by NURBS-Python\n")
            vertex_offset = 0  # count the vertices to update the face numbers correctly

            # Initialize lists for vertices, vertex normals and faces
            str_v = []
            str_vn = []
            str_f = []

            # Loop through MultiSurface object
            for surface in surface_list:
                if not isinstance(surface, Abstract.Surface):
                    warnings.warn("Encountered a non-surface object")
                    continue

                # Set surface delta
                surface.delta = surface_list.delta

                # Generate triangles
                vertices, triangles = _gen_triangles_vertices(surface.surfpts,
                                                              surface.sample_size, surface.sample_size,
                                                              vertex_spacing)

                # Collect vertices
                for vert_row in vertices:
                    for vert in vert_row:
                        line = "v " + str(vert.x) + " " + str(vert.y) + " " + str(vert.z) + "\n"
                        str_v.append(line)

                # Collect vertex normals
                for vert_row in vertices:
                    for vert in vert_row:
                        sn = surface.normal(vert.uv[0], vert.uv[1], True)
                        line = "vn " + str(sn[1][0]) + " " + str(sn[1][1]) + " " + str(sn[1][2]) + "\n"
                        str_vn.append(line)

                # Collect faces
                for t in triangles:
                    vl = t.vertex_ids
                    line = "f " + \
                           str(vl[0] + vertex_offset) + " " + \
                           str(vl[1] + vertex_offset) + " " + \
                           str(vl[2] + vertex_offset) + "\n"
                    str_f.append(line)

                # Update vertex offset
                vertex_offset = len(str_v)

            # Write all collected data to the file
            for line in str_v:
                fp.write(line)
            for line in str_vn:
                fp.write(line)
            for line in str_f:
                fp.write(line)
    except IOError:
        print("Cannot open " + str(file_name) + " for writing")


def save_stl_ascii_single(surface, **kwargs):
    """ Saves a single surface as an ASCII .stl file.

    :param surface: surface to be saved
    :type surface: Abstract.Surface

    Keyword Arguments:
        * file_name (str): name of the output file
        * vertex_spacing (int): size of the triangle edge in terms of points sampled on the surface

    """
    # Get keyword arguments
    file_name = kwargs.get('file_name', 'default.stl')
    vertex_spacing = kwargs.get('vertex_spacing', 2)

    # Input validity checking
    if not isinstance(surface, Abstract.Surface):
        raise ValueError("Input is not a surface")
    if vertex_spacing < 1 or not isinstance(vertex_spacing, int):
        raise ValueError("Vertex spacing must be an integer value and it must be bigger than zero")

    # Create the file and start saving triangulated surface points
    try:
        with open(file_name, 'w') as fp:
            vertices, triangles = _gen_triangles_vertices(surface.surfpts,
                                                          surface.sample_size, surface.sample_size,
                                                          vertex_spacing)

            fp.write("solid Surface\n")
            for t in triangles:
                line = "\tfacet normal " + str(t.normal[0]) + " " + str(t.normal[1]) + " " + str(t.normal[2]) + "\n"
                fp.write(line)
                fp.write("\t\touter loop\n")
                for v in t.vertices:
                    line = "\t\t\tvertex " + str(v.x) + " " + str(v.y) + " " + str(v.z) + "\n"
                    fp.write(line)
                fp.write("\t\tendloop\n")
                fp.write("\tendfacet\n")
            fp.write("endsolid Surface\n")
    except IOError:
        print("Cannot open " + str(file_name) + " for writing")


def save_stl_ascii_multi(surface_list, **kwargs):
    """ Saves multiple surfaces as an ASCII .stl file.

    :param surface_list: list of surfaces to be saved
    :type surface_list: Multi.MultiAbstract

    Keyword Arguments:
        * file_name (str): name of the output file
        * vertex_spacing (int): size of the triangle edge in terms of points sampled on the surface

    """
    # Get keyword arguments
    file_name = kwargs.get('file_name', 'default.stl')
    vertex_spacing = kwargs.get('vertex_spacing', 2)

    # Input validity checking
    if not isinstance(surface_list, Abstract.Multi):
        raise ValueError("Input must be a list of surfaces")
    if vertex_spacing < 1 or not isinstance(vertex_spacing, int):
        raise ValueError("Vertex spacing must be an integer value and it must be bigger than zero")

    # Create the file and start saving triangulated surface points
    try:
        with open(file_name, 'w') as fp:
            fp.write("solid Surface\n")

            # Loop through MultiSurface object
            for surface in surface_list:
                if not isinstance(surface, Abstract.Surface):
                    warnings.warn("Encountered a non-surface object")
                    continue

                # Set surface delta
                surface.delta = surface_list.delta

                vertices, triangles = _gen_triangles_vertices(surface.surfpts,
                                                              surface.sample_size, surface.sample_size,
                                                              vertex_spacing)

                for t in triangles:
                    line = "\tfacet normal " + str(t.normal[0]) + " " + str(t.normal[1]) + " " + str(t.normal[2]) + "\n"
                    fp.write(line)
                    fp.write("\t\touter loop\n")
                    for v in t.vertices:
                        line = "\t\t\tvertex " + str(v.x) + " " + str(v.y) + " " + str(v.z) + "\n"
                        fp.write(line)
                    fp.write("\t\tendloop\n")
                    fp.write("\tendfacet\n")

            fp.write("endsolid Surface\n")
    except IOError:
        print("Cannot open " + str(file_name) + " for writing")


def save_stl_binary_single(surface, **kwargs):
    """ Saves a single surface as a binary .stl file.

    Inspired from https://github.com/apparentlymart/python-stl

    :param surface: surface to be saved
    :type surface: Abstract.Surface

    Keyword Arguments:
        * file_name (str): name of the output file
        * vertex_spacing (int): size of the triangle edge in terms of points sampled on the surface

    """
    # Get keyword arguments
    file_name = kwargs.get('file_name', 'default.stl')
    vertex_spacing = kwargs.get('vertex_spacing', 2)

    # Input validity checking
    if not isinstance(surface, Abstract.Surface):
        raise ValueError("Input is not a surface")
    if vertex_spacing < 1 or not isinstance(vertex_spacing, int):
        raise ValueError("Vertex spacing must be an integer value and it must be bigger than zero")

    # Create the file and start saving triangulated surface points
    try:
        with open(file_name, 'wb') as fp:
            vertices, triangles = _gen_triangles_vertices(surface.surfpts,
                                                          surface.sample_size, surface.sample_size,
                                                          vertex_spacing)

            # Write triangle list to the binary STL file
            fp.write(b'\0' * 80)  # header
            fp.write(struct.pack('<i', len(triangles)))  # number of triangles
            for t in triangles:
                fp.write(struct.pack('<3f', *t.normal))  # normal
                for v in t.vertices:
                    fp.write(struct.pack('<3f', *v.data))  # vertices
                fp.write(b'\0\0')  # attribute byte count
    except IOError:
        print("Cannot open " + str(file_name) + " for writing")


def save_stl_binary_multi(surface_list, **kwargs):
    """ Saves multiple surfaces as a binary .stl file.

    :param surface_list: list of surfaces to be saved
    :type surface_list: Multi.MultiAbstract

    Keyword Arguments:
        * file_name (str): name of the output file
        * vertex_spacing (int): size of the triangle edge in terms of points sampled on the surface

    """
    # Get keyword arguments
    file_name = kwargs.get('file_name', 'default.stl')
    vertex_spacing = kwargs.get('vertex_spacing', 2)

    # Input validity checking
    if not isinstance(surface_list, Abstract.Multi):
        raise ValueError("Input must be a list of surfaces")
    if vertex_spacing < 1 or not isinstance(vertex_spacing, int):
        raise ValueError("Vertex spacing must be an integer value and it must be bigger than zero")

    # Create the file and start saving triangulated surface points
    try:
        with open(file_name, 'wb') as fp:
            # Loop through MultiSurface object
            triangles_list = []
            for surface in surface_list:
                if not isinstance(surface, Abstract.Surface):
                    warnings.warn("Encountered a non-surface object")
                    continue

                # Set surface delta
                surface.delta = surface_list.delta

                vertices, triangles = _gen_triangles_vertices(surface.surfpts,
                                                              surface.sample_size, surface.sample_size,
                                                              vertex_spacing)
                triangles_list += triangles

            # Write triangle list to the binary STL file
            fp.write(b'\0' * 80)  # header
            fp.write(struct.pack('<i', len(triangles_list)))  # number of triangles
            for t in triangles_list:
                fp.write(struct.pack('<3f', *t.normal))  # normal
                for v in t.vertices:
                    fp.write(struct.pack('<3f', *v.data))  # vertices
                fp.write(b'\0\0')  # attribute byte count
    except IOError:
        print("Cannot open " + str(file_name) + " for writing")


def save_off_single(surface, **kwargs):
    """ Saves a single surface as a .off file.

    :param surface: surface to be saved
    :type surface: Abstract.Surface

    Keyword Arguments:
        * file_name (str): name of the output file
        * vertex_spacing (int): size of the triangle edge in terms of points sampled on the surface

    """
    # Get keyword arguments
    file_name = kwargs.get('file_name', 'default.off')
    vertex_spacing = kwargs.get('vertex_spacing', 2)

    # Input validity checking
    if not isinstance(surface, Abstract.Surface):
        raise ValueError("Input is not a surface")
    if vertex_spacing < 1 or not isinstance(vertex_spacing, int):
        raise ValueError("Vertex spacing must be an integer value and it must be bigger than zero")

    # Create the file and start saving triangulated surface points
    try:
        with open(file_name, 'w') as fp:
            fp.write("OFF\n")
            vertices, triangles = _gen_triangles_vertices(surface.surfpts,
                                                          surface.sample_size, surface.sample_size,
                                                          vertex_spacing)

            line = str(len(vertices) * len(vertices[0])) + " " + str(len(triangles)) + " 0\n"
            fp.write(line)
            # Write vertices
            for vert_row in vertices:
                for vert in vert_row:
                    line = str(vert.x) + " " + str(vert.y) + " " + str(vert.z) + "\n"
                    fp.write(line)

            # Write faces (zero-indexed)
            for t in triangles:
                vl = t.vertex_ids
                line = "3 " + str(vl[0] - 1) + " " + str(vl[1] - 1) + " " + str(vl[2] - 1) + "\n"
                fp.write(line)
    except IOError:
        print("Cannot open " + str(file_name) + " for writing")


def save_off_multi(surface_list, **kwargs):
    """ Saves multiple surfaces as a single .off file.

    :param surface_list: list of surfaces to be saved
    :type surface_list: Multi.MultiSurface

    Keyword Arguments:
        * file_name (str): name of the output file
        * vertex_spacing (int): size of the triangle edge in terms of points sampled on the surface

    """
    # Get keyword arguments
    file_name = kwargs.get('file_name', 'default.off')
    vertex_spacing = kwargs.get('vertex_spacing', 2)

    # Input validity checking
    if not isinstance(surface_list, Multi.MultiSurface):
        raise ValueError("Input must be a list of surfaces")
    if vertex_spacing < 1 or not isinstance(vertex_spacing, int):
        raise ValueError("Vertex spacing must be an integer value and it must be bigger than zero")

    # Create the file and start saving triangulated surface points
    try:
        with open(file_name, 'w') as fp:
            vertex_offset = 0  # count the vertices to update the face numbers correctly

            # Initialize lists for vertices, vertex normals and faces
            str_v = []
            str_f = []

            # Loop through MultiSurface object
            for surface in surface_list:
                if not isinstance(surface, Abstract.Surface):
                    warnings.warn("Encountered a non-surface object")
                    continue

                # Set surface delta
                surface.delta = surface_list.delta

                # Generate triangles
                vertices, triangles = _gen_triangles_vertices(surface.surfpts,
                                                              surface.sample_size, surface.sample_size,
                                                              vertex_spacing)

                # Collect vertices
                for vert_row in vertices:
                    for vert in vert_row:
                        line = str(vert.x) + " " + str(vert.y) + " " + str(vert.z) + "\n"
                        str_v.append(line)

                # Collect faces (zero0indexed)
                for t in triangles:
                    vl = t.vertex_ids
                    line = "3 " + \
                           str(vl[0] - 1 + vertex_offset) + " " + \
                           str(vl[1] - 1 + vertex_offset) + " " + \
                           str(vl[2] - 1 + vertex_offset) + "\n"
                    str_f.append(line)

                # Update vertex offset
                vertex_offset = len(str_v)

            # Write file header
            fp.write("OFF\n")
            fp.write(str(len(str_v)) + " " + str(len(str_f)) + " 0\n")

            # Write all collected data to the file
            for line in str_v:
                fp.write(line)
            for line in str_f:
                fp.write(line)
    except IOError:
        print("Cannot open " + str(file_name) + " for writing")


def read_smesh(file_name):
    """ Generates a NURBS surface from a smesh file.

    *smesh* files are some text files which contain a set of NURBS surfaces. Each file in the set corresponds to one
    NURBS surface. Most of the time, you receive multiple *smesh* files corresponding to an complete object composed of
    several NURBS surfaces. The files have the extensions of ``txt`` or ``dat`` and they are named as

    * ``smesh.X.Y.txt``
    * ``smesh.X.dat``

    where *X* and *Y* correspond to some integer value which defines the set the surface belongs to and part number of
    the surface inside the complete object.

    This function reads a single smesh file and converts it into a NURBS surface. Please see the following functions
    for reading the smesh file sets:

    * :func:`.read_smesh_list()`
    * :func:`.read_smesh_dir()`

    :param file_name: smesh file to read
    :type file_name: str
    :return: a NURBS surface
    :rtype: NURBS.Surface
    """
    try:
        with open(file_name, 'r') as fp:
            content = fp.readlines()
            content = [x.strip().split() for x in content]
    except IOError:
        print("Cannot open " + str(file_name) + " for reading")
        return

    # 1st line defines the dimension and it must be 3
    if int(content[0][0]) != 3:
        warnings.warn("Input smesh file" + str(file_name) + " is not a surface")
        return

    # Create a NURBS surface instance and fill with the data read from smesh file
    surf = NURBS.Surface()

    # 2nd line is the degrees
    surf.degree_u = int(content[1][0])
    surf.degree_v = int(content[1][1])

    # 3rd line is the number of weighted control points in u and v directions
    dim_u = int(content[2][0])
    dim_v = int(content[2][1])
    ctrlpts_end = 5 + (dim_u * dim_v)

    # Starting from 6th line, we have the weighted control points
    ctrlpts_smesh = content[5:ctrlpts_end]

    # smesh files have the control points in u-row order format
    ctrlpts = compatibility.change_ctrlpts_row_order(ctrlpts_smesh, dim_u, dim_v)

    # smesh files store control points in format (x, y, z, w) -- Rhino format
    ctrlptsw = compatibility.generate_ctrlptsw(ctrlpts)

    # Set control points
    surf.set_ctrlpts(ctrlptsw, dim_u, dim_v)

    # 4th and 5th lines are knot vectors
    surf.knotvector_u = [float(u) for u in content[3]]
    surf.knotvector_v = [float(v) for v in content[4]]

    # Return the surface instance
    return surf


def read_smesh_list(file_list):
    """ Creates a MultiSurface instance from a list of smesh files.

    :param file_list: file list containing the names of the smesh files
    :type file_list: list, tuple
    :return: a MultiSurface instance containing all NURBS surfaces
    :rtype: Multi.MultiSurface
    """
    ret = Multi.MultiSurface()
    for file in file_list:
        ret.add(read_smesh(file))
    return ret


def read_smesh_dir(file_path):
    """ Creates a MultiSurface instance from a list of smesh files inside a directory.

    :param file_path: path to the directory containing smesh files
    :type file_path: str
    :return: a MultiSurface instance containing all NURBS surfaces
    :rtype: Multi.MultiSurface
    """
    files = sorted([os.path.join(file_path, f) for f in os.listdir(file_path)])
    return read_smesh_list(files)
