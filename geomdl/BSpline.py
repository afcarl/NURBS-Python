"""
.. module:: BSpline
    :platform: Unix, Windows
    :synopsis: A data storage and evaluation module for B-spline curves and surfaces

.. moduleauthor:: Onur Rauf Bingol <orbingol@gmail.com>

"""

from . import warnings
from . import copy
from . import pickle
from . import Abstract
from . import Multi
from . import utilities
from . import helpers
from . import evaluators


class Curve(Abstract.Curve):
    """ Data storage and evaluation class for B-Spline (NUBS) curves.

    The following properties are present in this class:

    * dimension
    * order
    * degree
    * knotvector
    * delta
    * ctrlpts
    * evalpts

    """

    def __init__(self):
        super(Curve, self).__init__()
        self._knot_vector = []
        self._control_points = []
        self._curve_points = []
        self._bounding_box = []
        self._evaluator = evaluators.CurveEvaluator()

    def __str__(self):
        return "B-Spline Curve"

    __repr__ = __str__

    def __call__(self, degree, ctrlpts, knotvector):
        self.reset(ctrlpts=True, evalpts=True)
        self.degree = degree
        self.ctrlpts = ctrlpts
        self.knotvector = knotvector

    @property
    def curvepts(self):
        return self.evalpts

    @property
    def ctrlpts(self):
        """ Control points.

        :getter: Gets the control points
        :setter: Sets the control points
        :type: list
        """
        ret_list = []
        for pt in self._control_points:
            ret_list.append(tuple(pt))
        return tuple(ret_list)

    @ctrlpts.setter
    def ctrlpts(self, value):
        self.set_ctrlpts(value)

    def set_ctrlpts(self, ctrlpts):
        """ Sets control points and checks if the data is consistent.

        :param ctrlpts: input control points as a list of coordinates
        :type ctrlpts: list
        :return: None
        """
        if len(ctrlpts) < self._degree + 1:
            raise ValueError("Number of control points should be at least degree + 1")

        # Clean up the curve and control points lists
        self.reset(ctrlpts=True, evalpts=True)

        # Estimate dimension by checking the size of the first element
        self._dimension = len(ctrlpts[0])

        for idx, cpt in enumerate(ctrlpts):
            if not isinstance(cpt, (list, tuple)):
                raise ValueError("Element number " + str(idx) + " is not a list")
            if len(cpt) is not self._dimension:
                raise ValueError("The input must be " + str(self._dimension) + " dimensional list - " + str(cpt) +
                                 " is not a valid control point")
            # Convert to list of floats
            coord_float = [float(coord) for coord in cpt]
            self._control_points.append(coord_float)

    @property
    def knotvector(self):
        """ Knot vector.

        :getter: Gets the knot vector
        :setter: Sets the knot vector
        :type: list
        """
        return tuple(self._knot_vector)

    @knotvector.setter
    def knotvector(self, value):
        if self._degree == 0 or not self._control_points:
            raise ValueError("Set degree and control points first")

        # Normalize the input knot vector
        value_normalized = utilities.normalize_knot_vector(value)

        # Check knot vector validity
        if not utilities.check_knot_vector(self._degree, value_normalized, len(self._control_points)):
            raise ValueError("Input is not a valid knot vector")

        # Clean up the surface points lists
        self.reset(evalpts=True)

        # Set knot vector
        self._knot_vector = [float(kv) for kv in value_normalized]

    def save(self, file_name):
        """  Saves the curve as a pickled file.

        :param file_name: name of the file to be saved
        :type file_name: str
        """
        # Create a dictionary from the curve data
        expdata = {'rational': self._rational,
                   'degree': self._degree,
                   'knotvector': self._knot_vector,
                   'ctrlpts': self._control_points,
                   'dimension': self._dimension}

        save_pickle(expdata, file_name)

    def load(self, file_name):
        """ Loads the curve from a pickled file.

        :param file_name: name of the file to be loaded
        :type file_name: str
        """
        impdata = read_pickle(file_name)

        if self._rational != impdata['rational']:
            raise TypeError("Curve types are not compatible (NURBS-BSpline mismatch)")

        # Clean control points and evaluated points
        self.reset(ctrlpts=True, evalpts=True)

        # Set the curve data
        self._degree = impdata['degree']
        self._knot_vector = impdata['knotvector']
        self._dimension = impdata['dimension']
        self._control_points = impdata['ctrlpts']

    def reset(self, **kwargs):
        """ Resets control or evaluated points.

        Keyword Arguments:

            * ``evalpts``: if True, then resets evaluated points
            * ``ctrlpts`` if True, then resets control points

        """
        reset_ctrlpts = kwargs.get('ctrlpts', False)
        reset_evalpts = kwargs.get('evalpts', False)

        if reset_ctrlpts:
            del self._control_points[:]
            del self._bounding_box[:]

        if reset_evalpts:
            del self._curve_points[:]

    def curvept(self, u):
        """ Evaluates the curve at the given parameter.

        :param u: parameter
        :type u: float
        :return: evaluated curve point
        :rtype: list
        """
        # Check all parameters are set before the curve evaluation
        self._check_variables()

        # Check u parameters are correct
        utilities.check_uv(u)

        # Evaluate
        cpt = self._evaluator.evaluate_single(knot=u,
                                              degree=self.degree,
                                              knotvector=self.knotvector,
                                              ctrlpts=self._control_points,
                                              dimension=self._dimension)

        return cpt

    def evaluate(self, **kwargs):
        """ Evaluates the curve.

        Keyword arguments:

        * ``start``: start parameter
        * ``stop``: stop parameter

        The ``start`` and ``stop`` parameters allow evaluation of a curve segment in the range *[start, stop]*, i.e.
        the curve will also be evaluated at the ``stop`` parameter value.

        .. note:: The evaluated curve points are stored in :py:attr:`~evalpts`.

        """
        # Check all parameters are set before the curve evaluation
        self._check_variables()

        # Find evaluation start and stop parameter values
        start = kwargs.get('start', self.knotvector[self.degree])
        stop = kwargs.get('stop', self.knotvector[-(self.degree+1)])

        # Check if the input parameters are in the range
        utilities.check_uv(start)
        utilities.check_uv(stop)

        # Clean up the curve points
        self.reset(evalpts=True)

        # Generate the knots in the range
        knots = utilities.linspace(start, stop, self.sample_size)

        # Evaluate
        cpts = self._evaluator.evaluate(knots=knots,
                                        degree=self.degree,
                                        knotvector=self.knotvector,
                                        ctrlpts=self._control_points,
                                        dimension=self._dimension)

        self._curve_points = cpts

    # Evaluates the curve derivative using "CurveDerivsAlg1" algorithm
    def derivatives2(self, u=-1, order=0):
        """ Evaluates n-th order curve derivatives at the given parameter value.

        Implements Algorithm A3.2 of *The NURBS Book*.

        :param u: knot value
        :type u: float
        :param order: derivative order
        :type order: integer
        :return: a list containing up to {order}-th derivative of the curve
        :rtype: list
        """
        # Check all parameters are set before the curve evaluation
        self._check_variables()
        # Check u parameters are correct
        utilities.check_uv(u)

        # Algorithm A3.2
        du = min(self._degree, order)

        CK = [[None for _ in range(self._dimension)] for _ in range(order + 1)]
        for k in range(self._degree + 1, order + 1):
            CK[k] = [0.0 for _ in range(self._dimension)]

        span = helpers.find_span(self.knotvector, len(self._control_points), u)
        bfunsders = helpers.basis_function_ders(self._degree, tuple(self._knot_vector), span, u, du)

        for k in range(0, du + 1):
            CK[k] = [0.0 for _ in range(self._dimension)]
            for j in range(0, self._degree + 1):
                CK[k][:] = [drv + (bfunsders[k][j] * ctrl_pt) for drv, ctrl_pt in
                            zip(CK[k], self._control_points[span - self._degree + j])]

        # Return the derivatives
        return CK

    # Computes the control points of all derivative curves up to and including the d-th derivative
    def derivatives_ctrlpts(self, order=0, r1=0, r2=0):
        """ Computes the control points of all derivative curves up to and including the {degree}-th derivative.

        Implements Algorithm A3.3 of *The NURBS Book*.
        Output is PK[k][i], i-th control point of the k-th derivative curve where 0 <= k <= degree and r1 <= i <= r2-k

        :param order: derivative order
        :type order: integer
        :param r1: minimum span
        :type r1: integer
        :param r2: maximum span
        :type r2: integer
        :return: PK, a 2D list of control points
        :rtype: list
        """
        # Algorithm A3.3
        r = r2 - r1
        PK = [[[None for _ in range(self._dimension)] for _ in range(r + 1)] for _ in range(order + 1)]
        for i in range(0, r + 1):
            PK[0][i][:] = [elem for elem in self._control_points[r1 + i]]

        for k in range(1, order + 1):
            tmp = self._degree - k + 1
            for i in range(0, r - k + 1):
                PK[k][i][:] = [tmp * (elem1 - elem2) / (
                    self._knot_vector[r1 + i + self._degree + 1] - self._knot_vector[r1 + i + k]) for elem1, elem2
                               in zip(PK[k - 1][i + 1], PK[k - 1][i])]

        return PK

    # Evaluates the curve derivative using "CurveDerivsAlg2" algorithm
    def derivatives(self, u=-1, order=0):
        """ Evaluates n-th order curve derivatives at the given parameter value.

        Implements Algorithm A3.4 of *The NURBS Book*.

        :param u: knot value
        :type u: float
        :param order: derivative order
        :type order: integer
        :return: a list containing up to {order}-th derivative of the curve
        :rtype: list
        """
        # Check all parameters are set before the curve evaluation
        self._check_variables()
        # Check u parameters are correct
        utilities.check_uv(u)

        # Algorithm A3.4
        du = min(self._degree, order)

        CK = [[None for _ in range(self._dimension)] for _ in range(order + 1)]
        for k in range(self._degree + 1, order + 1):
            CK[k] = [0.0 for _ in range(self._dimension)]

        span = helpers.find_span(self.knotvector, len(self._control_points), u)
        bfuns = helpers.basis_function_all(self._degree, tuple(self._knot_vector), span, u)
        PK = self.derivatives_ctrlpts(du, span - self._degree, span)

        for k in range(0, du + 1):
            CK[k] = [0.0 for _ in range(self._dimension)]
            for j in range(0, self._degree - k + 1):
                CK[k][:] = [elem + (bfuns[j][self._degree - k] * drv_ctrlpt) for elem, drv_ctrlpt in
                            zip(CK[k], PK[k][j])]

        # Return the derivatives
        return CK

    # Evaluates the curve tangent at the given u parameter
    def tangent(self, u=-1, normalize=False):
        """ Evaluates the curve tangent vector at the given parameter value.

        The output returns a list containing the starting point (i.e. origin) of the vector and the vector itself.

        :param u: knot value
        :type u: float
        :param normalize: if True, the returned vector is converted to a unit vector
        :type normalize: bool
        :return: a list in the order of "curve point" and "tangent"
        :rtype: list
        """
        # 1st derivative of the curve gives the tangent
        ders = self.derivatives(u, 1)

        # For readability
        point = ders[0]
        der_u = ders[1]

        # Normalize the tangent vector
        if normalize:
            der_u = utilities.vector_normalize(der_u)

        # Return the list
        return point, der_u

    # Evaluates the curve tangent at all u values in the input list
    def tangents(self, u_list=(), normalize=False):
        """ Evaluates the curve tangent vectors at all parameters values in the list of parameter values.

        :param u_list: list of parameter values
        :type u_list: tuple, list
        :param normalize: if True, the returned vector is converted to a unit vector
        :type normalize: bool
        :return: a list of starting points and the vectors
        :rtype: list
        """
        if not u_list or not isinstance(u_list, (tuple, list)):
            raise ValueError("Input u values must be a list/tuple of floats")

        ret_list = []
        for u in u_list:
            temp = self.tangent(u=u, normalize=normalize)
            ret_list.append(temp)

        return ret_list

    # Evaluates the curve normal at the given u parameter
    def normal(self, u=-1, normalize=True):
        """ Evaluates the curve normal vector at the given parameter value.

        Curve normal is basically the second derivative of the curve.
        The output returns a list containing the starting point (i.e. origin) of the vector and the vector itself.

        :param u: knot value
        :type u: float
        :param normalize: if True, the returned vector is converted to a unit vector
        :type normalize: bool
        :return: a list in the order of "curve point" and "normal"
        :rtype: list
        """
        # 2nd derivative of the curve gives the normal
        ders = self.derivatives(u, 2)

        # For readability
        point = ders[0]
        der_u = ders[2]

        # Normalize the normal vector
        if normalize:
            der_u = utilities.vector_normalize(der_u)

        # Return the list
        return point, der_u

    # Evaluates the curve normal at all u values in the input list
    def normals(self, u_list=(), normalize=False):
        """ Evaluates the curve normal at all parameters values in the list of parameter values.

        :param u_list: list of parameter values
        :type u_list: tuple, list
        :param normalize: if True, the returned vector is converted to a unit vector
        :type normalize: bool
        :return: a list of starting points and the vectors
        :rtype: list
        """
        if not u_list or not isinstance(u_list, (tuple, list)):
            raise ValueError("Input u values must be a list/tuple of floats")

        ret_list = []
        for u in u_list:
            temp = self.normal(u=u, normalize=normalize)
            ret_list.append(temp)

        return ret_list

    # Evaluates the curve binormal at the given u parameter
    def binormal(self, u=-1, normalize=True):
        """ Evaluates the curve binormal vector at the given u parameter.

        Curve binormal is the cross product of the normal and the tangent vectors.
        The output returns a list containing the starting point (i.e. origin) of the vector and the vector itself.

        :param u: knot value
        :type u: float
        :param normalize: if True, the returned vector is converted to a unit vector
        :type normalize: bool
        :return: a list in the order of "curve point" and "binormal"
        :rtype: list
        """
        tan_vector = self.tangent(u, normalize=normalize)
        norm_vector = self.normal(u, normalize=normalize)

        point = tan_vector[0]
        binorm_vector = utilities.vector_cross(tan_vector[1], norm_vector[1])

        # Normalize the binormal vector
        if normalize:
            binorm_vector = utilities.vector_normalize(binorm_vector)

        # Return the list
        return point, binorm_vector

    # Evaluates the curve binormal at all u values in the input list
    def binormals(self, u_list=(), normalize=False):
        """ Evaluates the curve binormal vectors at all parameters values in the list of parameter values.

        :param u_list: list of parameter values
        :type u_list: tuple, list
        :param normalize: if True, the returned vector is converted to a unit vector
        :type normalize: bool
        :return: a list of starting points and the vectors
        :rtype: list
        """
        if not u_list or not isinstance(u_list, (tuple, list)):
            raise ValueError("Input u values must be a list/tuple of floats")

        ret_list = []
        for u in u_list:
            temp = self.binormal(u=u, normalize=normalize)
            ret_list.append(temp)

        return ret_list

    # Knot insertion
    def insert_knot(self, u, r=1, check_r=True):
        """ Inserts the given knot and updates the control points array and the knot vector.

        :param u: knot to be inserted
        :type u: float
        :param r: number of knot insertions
        :type r: int
        :param check_r: enables/disables number of knot insertions check
        :type check_r: bool
        """
        # Check all parameters are set before the curve evaluation
        self._check_variables()
        # Check u parameters are correct
        utilities.check_uv(u)
        # Check if the number of knot insertions requested is valid
        if not isinstance(r, int) or r < 0:
            raise ValueError('Number of insertions (r) must be a positive integer value')

        s = helpers.find_multiplicity(u, self._knot_vector)

        # Check if it is possible add that many number of knots
        if check_r and r > self._degree - s:
            warnings.warn("Cannot insert " + str(r) + " number of knots")
            return

        # Algorithm A5.1
        k = helpers.find_span(self.knotvector, len(self._control_points), u)
        mp = len(self._knot_vector)
        np = len(self._control_points)
        nq = np + r

        # Initialize new knot vector array
        UQ = [None for _ in range(mp + r)]
        # Initialize new control points array (control points can be weighted or not)
        Q = [None for _ in range(nq)]
        # Initialize a local array of length p + 1
        R = [None for _ in range(self._degree + 1)]

        # Load new knot vector
        for i in range(0, k + 1):
            UQ[i] = self._knot_vector[i]
        for i in range(1, r + 1):
            UQ[k + i] = u
        for i in range(k + 1, mp):
            UQ[i + r] = self._knot_vector[i]

        # Save unaltered control points
        for i in range(0, k - self._degree + 1):
            Q[i] = self._control_points[i]
        for i in range(k - s, np):
            Q[i + r] = self._control_points[i]

        # The algorithm uses R array to update control points
        for i in range(0, self._degree - s + 1):
            R[i] = copy.deepcopy(self._control_points[k - self._degree + i])

        # Insert the knot r times
        for j in range(1, r + 1):
            L = k - self._degree + j
            for i in range(0, self._degree - j - s + 1):
                alpha = (u - self._knot_vector[L + i]) / (self._knot_vector[i + k + 1] - self._knot_vector[L + i])
                R[i][:] = [alpha * elem2 + (1.0 - alpha) * elem1 for elem1, elem2 in zip(R[i], R[i + 1])]
            Q[L] = copy.deepcopy(R[0])
            Q[k + r - j - s] = copy.deepcopy(R[self._degree - j - s])

        # Load remaining control points
        L = k - self._degree + r
        for i in range(L + 1, k - s):
            Q[i] = copy.deepcopy(R[i - L])

        # Update class variables
        self._knot_vector = UQ
        self._control_points = Q

        # Evaluate curve again if it has already been evaluated before knot insertion
        if check_r and self._curve_points:
            self.evaluate()

    def split(self, u=-1):
        """ Splits the curve at the input parametric coordinate.

        This method splits the curve into two pieces at the given parametric coordinate, generates two different
        curve objects and returns them. It doesn't change anything on the initial curve.

        :param u: parametric coordinate
        :type u: float
        :return: a list of curves as the split pieces of the initial curve
        :rtype: Multi.MultiCurve
        """
        # Validate input data
        if u == 0.0 or u == 1.0:
            raise ValueError("Cannot split on the corner points")
        utilities.check_uv(u)

        # Create backups of the original curve
        original_kv = copy.deepcopy(self._knot_vector)
        original_cpts = copy.deepcopy(self._control_points)

        # Find multiplicity of the knot
        ks = helpers.find_span(self.knotvector, len(self._control_points), u) - self._degree + 1
        s = helpers.find_multiplicity(u, self._knot_vector)
        r = self._degree - s

        # Insert knot
        self.insert_knot(u, r, check_r=False)

        # Knot vectors
        knot_span = helpers.find_span(self.knotvector, len(self._control_points), u) + 1
        curve1_kv = self._knot_vector[0:knot_span]
        curve1_kv.append(u)
        curve2_kv = self._knot_vector[knot_span:]
        for _ in range(0, self._degree + 1):
            curve2_kv.insert(0, u)

        # Control points
        curve1_ctrlpts = self._control_points[0:ks + r]
        curve2_ctrlpts = self._control_points[ks + r - 1:]

        # Create a new curve for the first half
        curve1 = self.__class__()
        curve1.degree = self.degree
        curve1.set_ctrlpts(curve1_ctrlpts)
        curve1.knotvector = curve1_kv

        # Create another curve fot the second half
        curve2 = self.__class__()
        curve2.degree = self.degree
        curve2.set_ctrlpts(curve2_ctrlpts)
        curve2.knotvector = curve2_kv

        # Restore the original curve
        self._knot_vector = original_kv
        self._control_points = original_cpts

        # Create a MultiCurve
        ret_val = Multi.MultiCurve()
        ret_val.add(curve1)
        ret_val.add(curve2)

        # Return the new curves as a MultiCurve object
        return ret_val

    def decompose(self):
        """ Decomposes the curve into Bezier curve segments of the same degree.

        This operation does not modify the curve, instead it returns the split curve segments.

        :return: a list of curve objects arranged in Bezier curve segments
        :rtype: Multi.MultiCurve
        """
        curve_list = Multi.MultiCurve()
        curve = copy.deepcopy(self)
        knots = curve.knotvector[curve.degree + 1:-(curve.degree + 1)]
        while knots:
            knot = knots[0]
            curves = curve.split(u=knot)
            curve_list.add(curves[0])
            curve = curves[1]
            knots = curve.knotvector[curve.degree + 1:-(curve.degree + 1)]
        curve_list.add(curve)

        return curve_list

    def translate(self, vec=()):
        """ Translates the curve by the input vector.

        The input vector list/tuple must have

        * 2 elements for 2D curves
        * 3 elements for 3D curves

        :param vec: translation vector
        :type vec: list, tuple
        """
        if not vec or not isinstance(vec, (tuple, list)):
            raise ValueError("The input must be a list or a tuple")

        if len(vec) != self._dimension:
            raise ValueError("The input must have " + str(self._dimension) + " elements")

        new_ctrlpts = []
        for point in self.ctrlpts:
            temp = [v + vec[i] for i, v in enumerate(point)]
            new_ctrlpts.append(temp)

        self.ctrlpts = new_ctrlpts

    def add_dimension(self):
        """ Converts x-D curve to a (x+1)-D curve.

        Useful when converting a 2-D curve to a 3-D curve.

        :return: curve object
        :rtype: Curve
        """
        dim = self._dimension
        if self._rational:
            dim -= 1

        # Update control points
        new_ctrlpts = []
        for point in self._control_points:
            temp = [float(p) for p in point[0:dim]]
            temp.append(0.0)
            if self._rational:
                temp.append(point[-1])
            new_ctrlpts.append(temp)

        # Convert to (x+1)-D curve, where x = self.dimension
        ret_val = self.__class__()
        ret_val.degree = self.degree
        ret_val.ctrlpts = new_ctrlpts
        ret_val.knotvector = self.knotvector
        ret_val.delta = self.delta

        return ret_val


class Surface(Abstract.Surface):
    """ Data storage and evaluation class for B-Spline (NUBS) surfaces.

    The following properties are present in this class:

    * dimension
    * order_u
    * order_v
    * degree_u
    * degree_v
    * knotvector_u
    * knotvector_v
    * delta
    * ctrlpts
    * ctrlpts2d
    * evalpts

    """

    def __init__(self):
        super(Surface, self).__init__()
        self._knot_vector_u = []
        self._knot_vector_v = []
        self._control_points = []
        self._control_points2D = []  # in [u][v] format
        self._surface_points = []
        self._bounding_box = []
        self._evaluator = evaluators.SurfaceEvaluator()

    def __str__(self):
        return "B-Spline Surface"

    __repr__ = __str__

    def __call__(self, degree_u, degree_v, ctrlpts_size_u, ctrlpts_size_v, ctrlpts, knotvector_u, knotvector_v):
        self.reset(evalpts=True, ctrlpts=True)
        self.degree_u = degree_u
        self.degree_v = degree_v
        self.set_ctrlpts(ctrlpts, ctrlpts_size_u, ctrlpts_size_v)
        self.knotvector_u = knotvector_u
        self.knotvector_v = knotvector_v

    @property
    def surfpts(self):
        return self.evalpts

    @property
    def ctrlpts(self):
        """ 1D Control points.

        .. note::

            The v index varies first. That is, a row of v control points for the first u value is found first.
            Then, the row of v control points for the next u value.

        :getter: Gets the control points
        :setter: Sets the control points
        :type: list
        """
        ret_list = []
        for pt in self._control_points:
            ret_list.append(tuple(pt))
        return tuple(ret_list)

    @ctrlpts.setter
    def ctrlpts(self, value):
        if self._control_points_size_u <= 0 and self._control_points_size_v <= 0:
            raise ValueError("Please set size of the control points in u and v directions")

        # Use set_ctrlpts directly
        self.set_ctrlpts(value, self._control_points_size_u, self._control_points_size_v)

    @property
    def ctrlpts2d(self):
        """ 2D control points.

        The getter returns a tuple of 2D control points (weighted control points + weights if NURBS) in *[u][v]* format.
        The rows of the returned tuple correspond to V-direction and the columns correspond to U-direction.

        The following example can be used to traverse 2D control points:

        .. code-block:: python

            # Create a BSpline surface
            surf_bs = BSpline.Surface()

            # Do degree, control points and knot vector assignments here

            # Each u includes a row of v values
            for u in surf_bs.ctrlpts2d:
                # Each row contains the coordinates of the control points
                for v in u:
                    print(str(v))  # will be something like (1.0, 2.0, 3.0)

            # Create a NURBS surface
            surf_nb = NURBS.Surface()

            # Do degree, weighted control points and knot vector assignments here

            # Each u includes a row of v values
            for u in surf_nb.ctrlpts2d:
                # Each row contains the coordinates of the weighted control points
                for v in u:
                    print(str(v))  # will be something like (0.5, 1.0, 1.5, 0.5)


        When using **NURBS.Surface** class, the output of :py:attr:`~ctrlpts2d` property could be confusing since,
        :py:attr:`~ctrlpts` always returns the unweighted control points, i.e. :py:attr:`~ctrlpts` property returns 3D
        control points all divided by the weights and you can use :py:attr:`~weights` property to access the weights
        vector, but :py:attr:`~ctrlpts2d` returns the weighted ones plus weights as the last element.
        This difference is intentionally added for compatibility and interoperability purposes.

        To explain this situation in a simple way;

        * If you need the weighted control points directly, use :py:attr:`~ctrlpts2d`
        * If you need the control points and the weights separately, use :py:attr:`~ctrlpts` and :py:attr:`~weights`

        .. note::

            Please note that the setter doesn't check for inconsistencies and using the setter is not recommended.
            Instead of the setter property, please use :func:`.set_ctrlpts()` function.

        :getter: Gets the control points in U and V directions
        :setter: Sets the control points in U and V directions
        :type: list
        """
        ret_list = []
        for u in range(0, self._control_points_size_u):
            ret_list_v = []
            for v in range(0, self._control_points_size_v):
                ret_list_v.append(tuple(self._control_points2D[u][v]))
            ret_list.append(tuple(ret_list_v))
        return tuple(ret_list)

    @ctrlpts2d.setter
    def ctrlpts2d(self, value):
        if not isinstance(value, (list, tuple)):
            raise ValueError("The input must be a list or tuple")

        # Clean up the surface and control points
        self.reset(evalpts=True, ctrlpts=True)

        # Assume that the user has prepared the lists correctly
        self._control_points_size_u = len(value)
        self._control_points_size_v = len(value[0])

        # Estimate dimension by checking the size of the first element
        self._dimension = len(value[0][0])

        # Make sure that all numbers are float type
        ctrlpts2d = [[None for _ in range(0, self._control_points_size_v)]
                     for _ in range(0, self._control_points_size_u)]
        for u in range(0, self._control_points_size_u):
            for v in range(0, self._control_points_size_v):
                ctrlpts2d[u][v] = [float(coord) for coord in value[u][v]]

        # Set 2D control points
        self._control_points2D = ctrlpts2d

        # Set 1D control points
        for u in self._control_points2D:
            for v in u:
                self._control_points.append(v)

    def set_ctrlpts(self, ctrlpts, size_u, size_v):
        """ Sets 1D control points.

        This function expects a list coordinates which is also a list. For instance, if you are working in 3D space,
        then your coordinates will be a list of 3 elements representing *(x, y, z)* coordinates.

        This function also generates 2D control points in *[u][v]* format which can be accessed via
        :py:attr:`~ctrlpts2d` property.

        .. note::

            The v index varies first. That is, a row of v control points for the first u value is found first.
            Then, the row of v control points for the next u value.

        :param ctrlpts: input control points as a list of coordinates
        :type ctrlpts: list
        :param size_u: size of the control points grid in U-direction
        :type size_u: int
        :param size_v: size of the control points grid in V-direction
        :type size_v: int
        :return: None
        """
        # Clean up the surface and control points
        self.reset(evalpts=True, ctrlpts=True)

        # Degree must be set before setting the control points
        if self._degree_u == 0 or self._degree_v == 0:
            raise ValueError("First, set the degrees!")

        # Check array size validity
        if size_u < self._degree_u + 1:
            raise ValueError("Number of control points in u-direction should be at least degree + 1")
        if size_v < self._degree_v + 1:
            raise ValueError("Number of control points in v-direction should be at least degree + 1")

        # Estimate dimension by checking the size of the first element
        self._dimension = len(ctrlpts[0])

        # Check the dimensions of the input control points array and type cast to float
        ctrlpts_float = []
        for idx, cpt in enumerate(ctrlpts):
            if not isinstance(cpt, (list, tuple)):
                raise ValueError("Element number " + str(idx) + " is not a list")
            if len(cpt) is not self._dimension:
                raise ValueError("The input must be " + str(self._dimension) + " dimensional list - " + str(cpt) +
                                 " is not a valid control point")
            pt_float = [float(coord) for coord in cpt]
            ctrlpts_float.append(pt_float)

        # Set the new control points
        self._control_points = ctrlpts_float

        # Set u and v sizes
        self._control_points_size_u = size_u
        self._control_points_size_v = size_v

        # Generate a 2D list of control points
        for i in range(0, self._control_points_size_u):
            ctrlpts_v = []
            for j in range(0, self._control_points_size_v):
                ctrlpts_v.append(self._control_points[j + (i * self._control_points_size_v)])
            self._control_points2D.append(ctrlpts_v)

    @property
    def knotvector_u(self):
        """ Knot vector for U direction.

        :getter: Gets the knot vector for U direction
        :setter: Sets the knot vector for U direction
        :type: list
        """
        return tuple(self._knot_vector_u)

    @knotvector_u.setter
    def knotvector_u(self, value):
        if self._degree_u == 0 or self._control_points_size_u == 0:
            raise ValueError("Set degree and control points first (u-direction)")

        # Normalize the input knot vector
        value_normalized = utilities.normalize_knot_vector(value)

        # Check knot vector validity
        if not utilities.check_knot_vector(self._degree_u, value_normalized, self._control_points_size_u):
            raise ValueError("Input is not a valid knot vector (u-direction)")

        # Clean up the surface points
        self.reset(evalpts=True)

        # Set knot vector u
        self._knot_vector_u = [float(kv) for kv in value_normalized]

    @property
    def knotvector_v(self):
        """ Knot vector for V direction.

        :getter: Gets the knot vector for V direction
        :setter: Sets the knot vector for V direction
        :type: list
        """
        return tuple(self._knot_vector_v)

    @knotvector_v.setter
    def knotvector_v(self, value):
        if self._degree_v == 0 or self._control_points_size_v == 0:
            raise ValueError("Set degree and control points first (v-direction)")

        # Normalize the input knot vector
        value_normalized = utilities.normalize_knot_vector(value)

        # Check knot vector validity
        if not utilities.check_knot_vector(self._degree_v, value_normalized, self._control_points_size_v):
            raise ValueError("Input is not a valid knot vector (v-direction)")

        # Clean up the surface points
        self.reset(evalpts=True)

        # Set knot vector v
        self._knot_vector_v = [float(kv) for kv in value_normalized]

    def save(self, file_name):
        """ Saves the surface as a pickled file.

        :param file_name: name of the file to be saved
        :type file_name: str
        """
        # Create a dictionary from the surface data
        expdata = {'rational': self._rational,
                   'degree_u': self._degree_u,
                   'degree_v': self._degree_v,
                   'knotvector_u': self._knot_vector_u,
                   'knotvector_v': self._knot_vector_v,
                   'ctrlpts_size_u': self._control_points_size_u,
                   'ctrlpts_size_v': self._control_points_size_v,
                   'ctrlpts': self._control_points,
                   'dimension': self._dimension}

        save_pickle(expdata, file_name)

    def load(self, file_name):
        """ Loads the surface from a pickled file.

        :param file_name: name of the file to be loaded
        :type file_name: str
        """
        impdata = read_pickle(file_name)

        # Check if we have loaded the correct type of surface
        if self._rational != impdata['rational']:
            raise TypeError("Surface types are not compatible (NURBS-BSpline mismatch)")

        # Clean control points and evaluated points
        self.reset(ctrlpts=True, evalpts=True)

        # Set the surface data
        self._degree_u = impdata['degree_u']
        self._degree_v = impdata['degree_v']
        self._knot_vector_u = impdata['knotvector_u']
        self._knot_vector_v = impdata['knotvector_v']
        self._control_points_size_u = impdata['ctrlpts_size_u']
        self._control_points_size_v = impdata['ctrlpts_size_v']
        self._dimension = impdata['dimension']
        self._control_points = impdata['ctrlpts']

    def reset(self, **kwargs):
        """ Resets control points and/or evaluated points.

        Keyword Arguments:

            * ``evalpts``: if True, then resets evaluated points
            * ``ctrlpts`` if True, then resets control points

        """
        reset_ctrlpts = kwargs.get('ctrlpts', False)
        reset_evalpts = kwargs.get('evalpts', False)

        if reset_ctrlpts:
            del self._control_points[:]
            del self._control_points2D[:]
            self._control_points_size_u = 0
            self._control_points_size_v = 0
            del self._bounding_box[:]

        if reset_evalpts:
            del self._surface_points[:]

    def transpose(self):
        """ Transposes the surface by swapping U and V directions. """
        # Transpose existing data
        degree_u_new = self._degree_v
        degree_v_new = self._degree_u
        kv_u_new = self._knot_vector_v
        kv_v_new = self._knot_vector_u
        ctrlpts2d_new = []
        for v in range(0, self._control_points_size_v):
            ctrlpts_u = []
            for u in range(0, self._control_points_size_u):
                temp = self._control_points2D[u][v]
                ctrlpts_u.append(temp)
            ctrlpts2d_new.append(ctrlpts_u)
        ctrlpts_new_size_u = self._control_points_size_v
        ctrlpts_new_size_v = self._control_points_size_u

        ctrlpts_new = []
        for v in range(0, ctrlpts_new_size_v):
            for u in range(0, ctrlpts_new_size_u):
                ctrlpts_new.append(ctrlpts2d_new[u][v])

        # Clean up the surface points
        self.reset(evalpts=True)

        # Save transposed data
        self._degree_u = degree_u_new
        self._degree_v = degree_v_new
        self._knot_vector_u = kv_u_new
        self._knot_vector_v = kv_v_new
        self._control_points = ctrlpts_new
        self._control_points_size_u = ctrlpts_new_size_u
        self._control_points_size_v = ctrlpts_new_size_v
        self._control_points2D = ctrlpts2d_new

    def surfpt(self, u, v):
        """ Evaluates the surface at the given (u,v) parameter.

        :param u: parameter in the U direction
        :type u: float
        :param v: parameter in the V direction
        :type v: float
        :return: evaluated surface point at the given knot values
        :rtype: list
        """
        # Check all parameters are set before the surface evaluation
        self._check_variables()

        # Check u and v parameters are correct
        utilities.check_uv(u, v)

        # Evaluate the surface
        spt = self._evaluator.evaluate_single(knot_u=u, knot_v=v,
                                              degree_u=self.degree_u, degree_v=self.degree_v,
                                              knotvector_u=self.knotvector_u, knotvector_v=self.knotvector_v,
                                              ctrlpts_size_u=self.ctrlpts_size_u, ctrlpts_size_v=self.ctrlpts_size_v,
                                              ctrlpts=self._control_points2D,
                                              dimension=self._dimension)

        return spt

    def evaluate(self, **kwargs):
        """ Evaluates the surface.

        Keyword arguments:

        * ``start_u``: start parameter in u-direction
        * ``stop_u``: stop parameter in u-direction
        * ``start_v``: start parameter in v-direction
        * ``stop_v``: stop parameter in v-direction

        The ``start_u``, ``start_v`` and ``stop_u`` and ``stop_v`` parameters allow evaluation of a surface segment
        in the range  *[start_u, stop_u][start_v, stop_v]* i.e. the surface will also be evaluated at the ``stop_u``
        and ``stop_v`` parameter values.

        .. note:: The evaluated surface points are stored in :py:attr:`~evalpts`.

        """
        # Check all parameters are set before the surface evaluation
        self._check_variables()

        # Find evaluation start and stop parameter values
        start_u = kwargs.get('start_u', self.knotvector_u[self.degree_u])
        stop_u = kwargs.get('stop_u', self.knotvector_u[-(self.degree_u+1)])
        start_v = kwargs.get('start_v', self.knotvector_v[self.degree_v])
        stop_v = kwargs.get('stop_v', self.knotvector_v[-(self.degree_v+1)])

        # Check if all the input parameters are in the range
        utilities.check_uv(start_u, stop_u)
        utilities.check_uv(start_v, stop_v)

        # Clean up the surface points
        self.reset(evalpts=True)

        # Compute knots in the range
        knots_u = utilities.linspace(start_u, stop_u, self.sample_size)
        knots_v = utilities.linspace(start_v, stop_v, self.sample_size)

        spts = self._evaluator.evaluate(knots_u=knots_u, knots_v=knots_v,
                                        degree_u=self.degree_u, degree_v=self.degree_v,
                                        knotvector_u=self.knotvector_u, knotvector_v=self.knotvector_v,
                                        ctrlpts_size_u=self.ctrlpts_size_u, ctrlpts_size_v=self.ctrlpts_size_v,
                                        ctrlpts=self._control_points2D,
                                        dimension=self._dimension)

        self._surface_points = spts

    # Evaluates n-th order surface derivatives at the given (u,v) parameter
    def derivatives(self, u=-1, v=-1, order=0):
        """ Evaluates n-th order surface derivatives at the given (u, v) parameter pair.

        * SKL[0][0] will be the surface point itself
        * SKL[0][1] will be the 1st derivative w.r.t. v
        * SKL[2][1] will be the 2nd derivative w.r.t. u and 1st derivative w.r.t. v

        :param u: parameter in the U direction
        :type u: float
        :param v: parameter in the V direction
        :type v: float
        :param order: derivative order
        :type order: integer
        :return: A list SKL, where SKL[k][l] is the derivative of the surface S(u,v) w.r.t. u k times and v l times
        :rtype: list
        """
        # Check all parameters are set before the surface evaluation
        self._check_variables()
        # Check u and v parameters are correct
        utilities.check_uv(u, v)

        # Algorithm A3.6
        du = min(self._degree_u, order)
        dv = min(self._degree_v, order)

        SKL = [[[0.0 for _ in range(self._dimension)] for _ in range(dv + 1)] for _ in range(du + 1)]

        span_u = helpers.find_span(self.knotvector_u, self._control_points_size_u, u)
        bfunsders_u = helpers.basis_function_ders(self._degree_u, self._knot_vector_u, span_u, u, du)
        span_v = helpers.find_span(self.knotvector_v, self._control_points_size_v, v)
        bfunsders_v = helpers.basis_function_ders(self._degree_v, self._knot_vector_v, span_v, v, dv)

        for k in range(0, du + 1):
            temp = [[] for _ in range(self._degree_v + 1)]
            for s in range(0, self._degree_v + 1):
                temp[s] = [0.0 for _ in range(self._dimension)]
                for r in range(0, self._degree_u + 1):
                    cu = span_u - self._degree_u + r
                    cv = span_v - self._degree_v + s
                    temp[s][:] = [tmp + (bfunsders_u[k][r] * cp) for tmp, cp in
                                  zip(temp[s], self._control_points2D[cu][cv])]

            dd = min(order - k, dv)
            for l in range(0, dd + 1):
                for s in range(0, self._degree_v + 1):
                    SKL[k][l][:] = [elem + (bfunsders_v[l][s] * tmp) for elem, tmp in zip(SKL[k][l], temp[s])]

        # Return the derivatives
        return SKL

    # Evaluates the surface tangent vectors at the given (u, v) parameter
    def tangent(self, u=-1, v=-1, normalize=False):
        """ Evaluates the surface tangent vector at the given (u, v) parameter pair.

        The output returns a list containing the starting point (i.e. origin) of the vector and the vectors themselves.

        :param u: parameter in the U direction
        :type u: float
        :param v: parameter in the V direction
        :type v: float
        :param normalize: if True, the returned tangent vector is converted to a unit vector
        :type normalize: bool
        :return: A list in the order of "surface point", "derivative w.r.t. u" and "derivative w.r.t. v"
        :rtype: list
        """
        # Tangent is the 1st derivative of the surface
        skl = self.derivatives(u, v, 1)

        # Doing this just for readability
        point = skl[0][0]
        der_u = skl[1][0]
        der_v = skl[0][1]

        # Normalize the tangent vectors
        if normalize:
            der_u = utilities.vector_normalize(der_u)
            der_v = utilities.vector_normalize(der_v)

        # Return the list of tangents w.r.t. u and v
        return tuple(point), der_u, der_v

    # Evaluates the surface tangent at all (u, v) values in the input list
    def tangents(self, uv_list=(), normalize=False):
        """ Evaluates the surface tangent vectors at all (u, v) parameter pairs in the input list.

        The input list should be arranged as [[u1, v1], [u2, v2], ...]

        :param uv_list: list of (u, v) parameter pairs
        :type uv_list: tuple, list
        :param normalize: if True, the returned vector is converted to a unit vector
        :type normalize: bool
        :return: a list of starting points and the vectors
        :rtype: list
        """
        if not uv_list or not isinstance(uv_list, (tuple, list)):
            raise ValueError("Input u, v values must be a list or a tuple")

        for uv in uv_list:
            if not isinstance(uv, (tuple, list)):
                raise ValueError("The list member " + str(uv) + " is not a tuple or a list")
            if len(uv) is not 2:
                raise ValueError("The list member " + str(uv) + " does not correspond to a (u, v) value")

        ret_list = []
        for u, v in uv_list:
            temp = self.tangent(u=u, v=v, normalize=normalize)
            ret_list.append(temp)

        return ret_list

    # Evaluates the surface normal vector at the given (u, v) parameter
    def normal(self, u=-1, v=-1, normalize=True):
        """ Evaluates the surface normal vector at the given (u, v) parameter pair.

        The output returns a list containing the starting point (i.e. origin) of the vector and the vector itself.

        :param u: parameter in the U direction
        :type u: float
        :param v: parameter in the V direction
        :type v: float
        :param normalize: if True, the returned normal vector is converted to a unit vector
        :type normalize: bool
        :return: a list in the order of "surface point" and "normal vector"
        :rtype: list
        """
        # Check u and v parameters are correct for the normal evaluation
        utilities.check_uv(u, v)

        # Take the 1st derivative of the surface
        skl = self.derivatives(u, v, 1)

        # For readability
        der_u = skl[1][0]
        der_v = skl[0][1]

        # Compute normal
        normal = utilities.vector_cross(der_u, der_v)

        if normalize:
            # Convert normal vector to a unit vector
            normal = utilities.vector_normalize(tuple(normal))

        # Return the surface normal at the input u,v location
        return skl[0][0], normal

    # Evaluates the surface normal at all (u, v) values in the input list
    def normals(self, uv_list=(), normalize=False):
        """ Evaluates the surface normal at all (u, v) parameter pairs in the input list.

        The input list should be arranged as [[u1, v1], [u2, v2], ...]

        :param uv_list: list of (u, v) parameter pairs
        :type uv_list: tuple, list
        :param normalize: if True, the returned vector is converted to a unit vector
        :type normalize: bool
        :return: a list of starting points and the vectors
        :rtype: list
        """
        if not uv_list or not isinstance(uv_list, (tuple, list)):
            raise ValueError("Input u, v values must be a list or a tuple")

        for uv in uv_list:
            if not isinstance(uv, (tuple, list)):
                raise ValueError("The list member " + str(uv) + " is not a tuple or a list")
            if len(uv) is not 2:
                raise ValueError("The list member " + str(uv) + " does not correspond to a (u, v) value")

        ret_list = []
        for u, v in uv_list:
            temp = self.normal(u=u, v=v, normalize=normalize)
            ret_list.append(temp)

        return ret_list

    # Insert knot 'r' times at the given (u, v) parametric coordinates
    def insert_knot(self, u=None, v=None, ru=1, rv=1, check_r=True):
        """ Inserts the given knots and updates the control points array and the knot vectors.

        :param u: Knot to be inserted in U-direction
        :type u: float
        :param v: Knot to be inserted in V-direction
        :type v: float
        :param ru: Number of knot insertions in U-direction
        :type ru: int
        :param rv: Number of knot insertions in V-direction
        :type rv: int
        :param check_r: enables/disables number of knot insertions check
        :type check_r: bool
        """
        can_insert_knot = True

        # Check all parameters are set before the curve evaluation
        self._check_variables()

        # Check if the parameter values are correctly defined
        if u or v:
            utilities.check_uv(u, v)

        if not isinstance(ru, int) or ru < 0:
            raise ValueError("Number of insertions in U-direction must be a positive integer")

        if not isinstance(rv, int) or rv < 0:
            raise ValueError("Number of insertions in V-direction must be a positive integer")

        # Algorithm A5.3
        p = self._degree_u
        q = self._degree_v

        if u:
            np = self._control_points_size_u
            mp = self._control_points_size_v

            s_u = helpers.find_multiplicity(u, self._knot_vector_u)

            # Check if it is possible add that many number of knots
            if check_r and ru > p - s_u:
                warnings.warn("Cannot insert " + str(ru) + " knots in the U direction")
                can_insert_knot = False

            if can_insert_knot:
                k_u = helpers.find_span(self.knotvector_u, self._control_points_size_u, u)

                # Initialize new knot vector array
                UQ = [None for _ in range(len(self._knot_vector_u) + ru)]
                # Initialize new control points array (control points can be weighted or not)
                Q = [[None for _ in range(self._control_points_size_v)]
                     for _ in range(self._control_points_size_u + ru)]
                # Initialize a local array of length p + 1
                R = [None for _ in range(p + 1)]

                # Load new knot vector
                for i in range(0, k_u + 1):
                    UQ[i] = self._knot_vector_u[i]
                for i in range(1, ru + 1):
                    UQ[k_u + i] = u
                for i in range(k_u + 1, len(self._knot_vector_u)):
                    UQ[i + ru] = self._knot_vector_u[i]

                # Save the alphas
                alpha = [[0.0 for _ in range(ru + 1)] for _ in range(p - s_u)]
                for j in range(1, ru + 1):
                    L = k_u - p + j
                    for i in range(0, p - j - s_u + 1):
                        alpha[i][j] = (u - self._knot_vector_u[L + i]) / (
                            self._knot_vector_u[i + k_u + 1] - self._knot_vector_u[L + i])

                # For each row do
                for row in range(0, mp):
                    for i in range(0, k_u - p + 1):
                        Q[i][row] = self._control_points2D[i][row]
                    for i in range(k_u - s_u, np):
                        Q[i + ru][row] = self._control_points2D[i][row]
                    # Load auxiliary control points
                    for i in range(0, p - s_u + 1):
                        R[i] = copy.deepcopy(self._control_points2D[k_u - p + i][row])
                    # Insert the knot r times
                    for j in range(1, ru + 1):
                        L = k_u - p + j
                        for i in range(0, p - j - s_u + 1):
                            R[i][:] = [alpha[i][j] * elem2 + (1.0 - alpha[i][j]) * elem1 for elem1, elem2 in
                                       zip(R[i], R[i + 1])]
                        Q[L][row] = copy.deepcopy(R[0])
                        Q[k_u + ru - j - s_u][row] = copy.deepcopy(R[p - j - s_u])
                    # Load the remaining control points
                    L = k_u - p + ru
                    for i in range(L + 1, k_u - s_u):
                        Q[i][row] = copy.deepcopy(R[i - L])

                # Update class variables after knot insertion
                self._knot_vector_u = UQ
                self._control_points2D = Q
                self._control_points_size_u += ru
                # Update 1D control points
                self._control_points[:] = []
                for dir_u in self._control_points2D:
                    for dir_v in dir_u:
                        self._control_points.append(dir_v)

        if v:
            np = self._control_points_size_u
            mp = self._control_points_size_v

            s_v = helpers.find_multiplicity(v, self._knot_vector_v)

            # Check if it is possible add that many number of knots
            if check_r and rv > q - s_v:
                warnings.warn("Cannot insert " + str(rv) + " knots in the V direction")
                can_insert_knot = False

            if can_insert_knot:
                k_v = helpers.find_span(self.knotvector_v, self._control_points_size_v, v)

                # Initialize new knot vector array
                VQ = [None for _ in range(len(self._knot_vector_v) + rv)]
                # Initialize new control points array (control points can be weighted or not)
                Q = [[None for _ in range(self._control_points_size_v + rv)]
                     for _ in range(self._control_points_size_u)]
                # Initialize a local array of length q + 1
                R = [None for _ in range(q + 1)]

                # Load new knot vector
                for i in range(0, k_v + 1):
                    VQ[i] = self._knot_vector_v[i]
                for i in range(1, rv + 1):
                    VQ[k_v + i] = v
                for i in range(k_v + 1, len(self._knot_vector_v)):
                    VQ[i + rv] = self._knot_vector_v[i]

                # Save the alphas
                alpha = [[0.0 for _ in range(rv + 1)] for _ in range(q - s_v)]
                for j in range(1, rv + 1):
                    L = k_v - q + j
                    for i in range(0, q - j - s_v + 1):
                        alpha[i][j] = (v - self._knot_vector_v[L + i]) / (
                            self._knot_vector_v[i + k_v + 1] - self._knot_vector_v[L + i])

                # For each row do
                for col in range(0, np):
                    for i in range(0, k_v - q + 1):
                        Q[col][i] = self._control_points2D[col][i]
                    for i in range(k_v - s_v, mp):
                        Q[col][i + rv] = self._control_points2D[col][i]
                    # Load auxiliary control points
                    for i in range(0, q - s_v + 1):
                        R[i] = copy.deepcopy(self._control_points2D[col][k_v - q + i])
                    # Insert the knot r times
                    for j in range(1, rv + 1):
                        L = k_v - q + j
                        for i in range(0, q - j - s_v + 1):
                            R[i][:] = [alpha[i][j] * elem2 + (1.0 - alpha[i][j]) * elem1 for elem1, elem2 in
                                       zip(R[i], R[i + 1])]
                        Q[col][L] = copy.deepcopy(R[0])
                        Q[col][k_v + rv - j - s_v] = copy.deepcopy(R[q - j - s_v])
                    # Load the remaining control points
                    L = k_v - q + rv
                    for i in range(L + 1, k_v - s_v):
                        Q[col][i] = copy.deepcopy(R[i - L])

                # Update class variables after knot insertion
                self._knot_vector_v = VQ
                self._control_points2D = Q
                self._control_points_size_v += rv
                # Update 1D control points
                self._control_points[:] = []
                for dir_u in self._control_points2D:
                    for dir_v in dir_u:
                        self._control_points.append(dir_v)

        # Evaluate surface again if it has already been evaluated before knot insertion
        if check_r and self._surface_points:
            self.evaluate()

    def split_u(self, t=-1):
        """ Splits the surface at the input parametric coordinate in U-direction.

        This method splits the surface into two pieces at the given parametric coordinate in U-direction,
        generates two different surface objects and returns them. It doesn't change anything on the initial surface.

        :param t: parametric coordinate in U-direction
        :type t: float
        :return: a list of surface as the split pieces of the initial surface
        :rtype: Multi.MultiSurface
        """
        # Validate input data
        if t == 0.0 or t == 1.0:
            raise ValueError("Cannot split on the corner points")
        utilities.check_uv(t)

        # Create backups of the original surface
        original_kv = copy.deepcopy(self._knot_vector_u)
        original_cpts = copy.deepcopy(self._control_points)
        original_cpts_size_u = copy.deepcopy(self.ctrlpts_size_u)
        original_cpts_size_v = copy.deepcopy(self.ctrlpts_size_v)

        # Find multiplicity of the knot
        ks = helpers.find_span(self.knotvector_u, self.ctrlpts_size_u, t) - self._degree_u + 1
        s = helpers.find_multiplicity(t, self._knot_vector_u)
        r = self._degree_u - s

        # Split the original surface
        self.insert_knot(u=t, ru=r, check_r=False)

        # Knot vectors
        knot_span = helpers.find_span(self.knotvector_u, self.ctrlpts_size_u, t) + 1
        surf1_kv = self._knot_vector_u[0:knot_span]
        surf1_kv.append(t)
        surf2_kv = self._knot_vector_u[knot_span:]
        for _ in range(0, self._degree_u + 1):
            surf2_kv.insert(0, t)

        # Control points
        surf1_ctrlpts = self._control_points2D[0:ks + r]
        surf2_ctrlpts = self._control_points2D[ks + r - 1:]

        # Create a new surface for the first half
        surf1 = self.__class__()
        surf1.degree_u = self.degree_u
        surf1.degree_v = self.degree_v
        surf1.ctrlpts2d = surf1_ctrlpts
        surf1.knotvector_u = surf1_kv
        surf1.knotvector_v = self.knotvector_v

        # Create another surface fot the second half
        surf2 = self.__class__()
        surf2.degree_u = self.degree_u
        surf2.degree_v = self.degree_v
        surf2.ctrlpts2d = surf2_ctrlpts
        surf2.knotvector_u = surf2_kv
        surf2.knotvector_v = self.knotvector_v

        # Restore the original surface
        self.ctrlpts_size_u = original_cpts_size_u
        self.ctrlpts_size_v = original_cpts_size_v
        self.ctrlpts = original_cpts
        self.knotvector_u = original_kv

        # Create a MultiSurface
        ret_val = Multi.MultiSurface()
        ret_val.add(surf1)
        ret_val.add(surf2)

        # Return the new surfaces
        return ret_val

    def split_v(self, t=-1):
        """ Splits the surface at the input parametric coordinate in V-direction.

        This method splits the surface into two pieces at the given parametric coordinate in V-direction,
        generates two different surface objects and returns them. It doesn't change anything on the initial surface.

        :param t: parametric coordinate in U-direction
        :type t: float
        :return: a list of surface as the split pieces of the initial surface
        :rtype: Multi.MultiSurface
        """
        # Validate input data
        if t == 0.0 or t == 1.0:
            raise ValueError("Cannot split on the corner points")
        utilities.check_uv(t)

        # Create backups of the original surface
        original_kv = copy.deepcopy(self._knot_vector_v)
        original_cpts = copy.deepcopy(self._control_points)
        original_cpts_size_u = copy.deepcopy(self.ctrlpts_size_u)
        original_cpts_size_v = copy.deepcopy(self.ctrlpts_size_v)

        # Find multiplicity of the knot
        ks = helpers.find_span(self.knotvector_v, self.ctrlpts_size_v, t) - self._degree_v + 1
        s = helpers.find_multiplicity(t, self._knot_vector_v)
        r = self._degree_v - s

        # Split the original surface
        self.insert_knot(v=t, rv=r, check_r=False)

        # Knot vectors
        knot_span = helpers.find_span(self.knotvector_v, self.ctrlpts_size_v, t) + 1
        surf1_kv = self._knot_vector_v[0:knot_span]
        surf1_kv.append(t)
        surf2_kv = self._knot_vector_v[knot_span:]
        for _ in range(0, self._degree_v + 1):
            surf2_kv.insert(0, t)

        # Control points
        surf1_ctrlpts = []
        for v_row in self._control_points2D:
            temp = v_row[0:ks + r]
            surf1_ctrlpts.append(temp)
        surf2_ctrlpts = []
        for v_row in self._control_points2D:
            temp = v_row[ks + r - 1:]
            surf2_ctrlpts.append(temp)

        # Create a new surface for the first half
        surf1 = self.__class__()
        surf1.degree_u = self.degree_u
        surf1.degree_v = self.degree_v
        surf1.ctrlpts2d = surf1_ctrlpts
        surf1.knotvector_v = surf1_kv
        surf1.knotvector_u = self.knotvector_u

        # Create another surface fot the second half
        surf2 = self.__class__()
        surf2.degree_u = self.degree_u
        surf2.degree_v = self.degree_v
        surf2.ctrlpts2d = surf2_ctrlpts
        surf2.knotvector_v = surf2_kv
        surf2.knotvector_u = self.knotvector_u

        # Restore the original surface
        self.ctrlpts_size_u = original_cpts_size_u
        self.ctrlpts_size_v = original_cpts_size_v
        self.ctrlpts = original_cpts
        self.knotvector_v = original_kv

        # Create a MultiSurface
        ret_val = Multi.MultiSurface()
        ret_val.add(surf1)
        ret_val.add(surf2)

        # Return the new surfaces
        return ret_val

    def decompose(self):
        """ Decomposes the surface into Bezier surface patches of the same degree.

        This operation does not modify the surface, instead it returns the surface patches.

        :return: a list of surface objects arranged as Bezier surface patches
        :rtype: Multi.MultiSurface
        """
        surf_list = []

        # Work with an identical copy
        surf = copy.deepcopy(self)

        # U-direction
        knots_u = surf.knotvector_u[surf.degree_u + 1:-(surf.degree_u + 1)]
        while knots_u:
            knot = knots_u[0]
            surfs = surf.split_u(t=knot)
            surf_list.append(surfs[0])
            surf = surfs[1]
            knots_u = surf.knotvector_u[surf.degree_u + 1:-(surf.degree_u + 1)]
        surf_list.append(surf)

        # Work on the split surfaces in V-direction
        multi_surf = Multi.MultiSurface()
        for surf in surf_list:
            knots_v = surf.knotvector_v[surf.degree_v + 1:-(surf.degree_v + 1)]
            while knots_v:
                knot = knots_v[0]
                surfs = surf.split_v(t=knot)
                multi_surf.add(surfs[0])
                surf = surfs[1]
                knots_v = surf.knotvector_v[surf.degree_v + 1:-(surf.degree_v + 1)]
            multi_surf.add(surf)

        return multi_surf

    def translate(self, vec=()):
        """ Translates the surface by the input vector.

        :param vec: translation vector in 3D
        :type vec: list, tuple
        """
        if not vec or not isinstance(vec, (tuple, list)):
            raise ValueError("The input must be a list or a tuple")

        if len(vec) != self._dimension:
            raise ValueError("The input must have " + str(self._dimension) + " elements")

        new_ctrlpts = []
        for point in self.ctrlpts:
            temp = [v + vec[i] for i, v in enumerate(point)]
            new_ctrlpts.append(temp)

        self.ctrlpts = new_ctrlpts


def save_pickle(data_dict, file_name):
    """ Saves the contents of the data dictionary as a pickled file.

    Helper function for curve and surface ``save`` method.

    :param data_dict: data dictionary
    :type data_dict: dict
    :param file_name: name of the file to be saved
    :type file_name: str
    """
    # Try opening the file for writing
    try:
        with open(file_name, 'wb') as fp:
            # Pickle the data dictionary
            pickle.dump(data_dict, fp)
    except IOError:
        # Show a warning on failure to open file
        warnings.warn("File " + str(file_name) + " cannot be opened for writing.")


def read_pickle(file_name):
    """ Reads a data dictionary from a pickled file.

    Helper function for curve and surface ``load`` method.

    :param file_name: name of the file to be loaded
    :type file_name: str
    :return: data dictionary
    :rtype: dict
    """
    # Try opening the file for reading
    try:
        with open(file_name, 'rb') as fp:
            # Read and return the pickled file
            impdata = pickle.load(fp)
            return impdata
    except IOError:
        # Raise an exception on failure to open file
        raise IOError("File " + str(file_name) + " cannot be opened for reading.")
