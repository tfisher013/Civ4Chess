def are_plots_equal(plot_1, plot_2):
    """
    Determines whether two CyPlot objects are equal by comparing
    their X and Y coordinates.

    Args:
        plot_1: a CyPlot object
        plot_2: a CyPlot object

    Returns:
        True if the plots represent the same tile on the map, False otherwise
    """

    return plot_1.getX() == plot_2.getX() and plot_1.getY() == plot_2.getY()


def are_units_equal(unit_1, unit_2):
    """
    Determines whether the two provided CyUnit objects represent the same unit in play

    Args:
        unit_1: a CyUnit object
        unit_2: a CyUnit object

    Returns:
        True if the objects represent the same unit in play, False otherwise
    """

    if unit_1.getID() != unit_2.getID():
        return False
    if unit_1.getMoves() != unit_2.getMoves():
        return False
    if unit_1.movesLeft() != unit_2.movesLeft():
        return False
    if unit_1.getOwner() != unit_2.getOwner():
        return False
    if unit_1.getX() != unit_2.getX():
        return False
    if unit_1.getY() != unit_2.getY():
        return False

    return True