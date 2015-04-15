# Internal modules
import pymel.core as pm

# External modules
from pipeline import cfb
from pipeline.maya import asset
from pipeline.maya import sort
from pipeline.maya import project

from pipeline.database.team import Team
import pipeline.vray.utils as utils

# Built-in modules
import os.path
import re

def factory( *a ):
    ## INITIALIZE V-RAY SETTINGS
    #pm.Mel.eval('unifiedRenderGlobalsWindow;')
    #try:
    #utils.initVray()
    #utils.setVrayDefaults()

    asset.reference(cfb.FACTORY_LIGHT_RIG, 'FACTORY')
    sc = sort.SortControl('Factory')
    sc.run()


def loadTeams(home, away=None, clean=True, *a):
    ''' Loads a home team and an optional away team into the scene.  Includes many checks, but 
        also makes many assumptions about the scenes preparedness in the pipeline. '''
    loadAssets(home, 'HOME', clean)
    if away:
        loadAssets(away, 'AWAY', clean)
    return


def loadAssets(tricode, location, clean=True):
    ''' Load the selected team sign and logo pair into the specified 'location' (home/away)
        as a namespace. In clean mode, it removes any existing references and creates fresh 
        constraints. In 'dirty' mode, it will simply replace the existing references. '''

    # Get team info from database
    try:
        team = Team(tricode)
    except: 
        pm.warning('Build Scene  ERROR Could not find team in database.')
        return

    # Generate string for the name of the school's sign
    sign = 'SIGN_{0}'.format(team.sign.upper())

    # Create paths for signs / team logo scenes
    sign_path = os.path.join(cfb.MAIN_ASSET_DIR, sign, (sign+'.mb'))
    logo_path = os.path.join(cfb.TEAMS_ASSET_DIR, team.tricode, (team.tricode+'.mb'))

    # Generate namespaces
    sign_nspc = '{0}SIGN'.format(location)
    logo_nspc = '{0}LOGO'.format(location)

    # Check for existing references
    sign_ref = None
    logo_ref = None

    # Get those reference nodess
    for ref in pm.listReferences():
        if ref.namespace == sign_nspc:
            sign_ref = ref

        elif ref.namespace == logo_nspc:
            logo_ref = ref

    # If there are references missing, force a clean run for simplicity's sake (i implore you)
    if (sign_ref) or (logo_ref) == None and clean == False:
        pm.warning('Build Scene  WARNING Existing reference not found.  Forcing clean reference.')
        clean = True

    # If the user has asked to do a clean reference of the asset, including attachment
    if (clean):
        # If there's already references in those namespaces, just delete them
        if (logo_ref): logo_ref.remove()
        if (sign_ref): sign_ref.remove()
        # Reference in the asset to the namespace
        asset.reference(sign_path, sign_nspc)
        asset.reference(logo_path, logo_nspc)
        # Attach them to their parent locators
        attachToSign(location)
        attachToScene(location)

    # (If) there are already references in the namespaces, and the user is requesting
    # to replace the reference and maintain reference edits (dirty mode)
    elif not (clean):
        # If the right sign is already loaded, pass
        if (sign+'.mb') in sign_ref.path:
            pass
        # Or else replace the sign reference
        else:
            sign_ref.replaceWith(sign_path)
        # Same thing with school logos this time
        if (team.tricode+'.mb') in logo_ref.path:
            pass
        else:
            logo_ref.replaceWith(logo_path)

    # Cleanup foster parents
    try:
        sign_re = re.compile('{0}RNfosterParent.'.format(sign_nspc))
        logo_re = re.compile('{0}RNfosterParent.'.format(logo_nspc))

        pm.delete(pm.ls(regex=sign_re))
        pm.delete(pm.ls(regex=logo_re))
    except:
        pass


def attachToSign(location):
    ''' Attaches a team logo to its corresponding sign.  Location refers to home/away. '''
    location = location.upper()

    sign_namespace = '{0}SIGN'.format(location)
    logo_namespace = '{0}LOGO'.format(location)

    # Get basic attachment points
    try:
        sign_atch_board  = pm.PyNode('{0}:ATTACH_01'.format(sign_namespace))
        sign_atch_bldg   = pm.PyNode('{0}:ATTACH_05'.format(sign_namespace))
        sign_atch_mascot = pm.PyNode('{0}:ATTACH_06'.format(sign_namespace))

        logo_atch_board  = pm.PyNode('{0}:ATTACH_01'.format(logo_namespace))

    except:
        pm.warning('Build Scene  ERROR Critical attachment points not found for {0} team.'.format(location))
    
    # Get optional attachment points.  These do not exist in every element.
    try:
        logo_atch_bldg   = pm.PyNode('{0}:ATTACH_05'.format(logo_namespace))
    except: logo_atch_bldg = None
    try:
        logo_atch_mascot = pm.PyNode('{0}:ATTACH_06'.format(logo_namespace))
    except: logo_atch_mascot = None

    attach(sign_atch_board, logo_atch_board)
    if (logo_atch_bldg):
        attach(sign_atch_bldg, logo_atch_bldg)
    if (logo_atch_mascot):
        attach(sign_atch_mascot, logo_atch_mascot)    
    return


def attachToScene(location):
    ''' Attaches a sign to its corresponding locator in the scene.  Location refers to home/away '''
    location = location.upper()

    sign_namespace = '{0}SIGN'.format(location)

    # Check for attachment locators
    try:
        scene_loc = pm.PyNode('{0}_LOCATOR'.format(location))
    except: 
        pm.warning('Build Scene  ERROR Missing sign attachment locator for {0} team.'.format(location))
        return

    try:
        sign_loc = pm.PyNode('{0}SIGN:MAIN_POS'.format(location))
    except:
        pm.warning('Build Scene  ERROR Could not find sign master control curve for {0} team.'.format(location))
        return

    attach(scene_loc, sign_loc)
    return


def attach(parent, child):
    ''' Combines parent and scale constraining into one command. '''
    pc = pm.parentConstraint(parent, child, mo=False)
    sc = pm.scaleConstraint(parent, child, mo=False)
    return (pc,sc)


