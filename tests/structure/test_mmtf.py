# This source code is part of the Biotite package and is distributed
# under the 3-Clause BSD License. Please see 'LICENSE.rst' for further
# information.

import biotite.structure as struc
import biotite.structure.io.mmtf as mmtf
import biotite.structure.io.pdbx as pdbx
import numpy as np
import glob
import itertools
from os.path import join, basename
from .util import data_dir
import pytest
from pytest import approx


@pytest.mark.parametrize("path", glob.glob(join(data_dir, "*.mmtf")))
def test_codecs(path):
    mmtf_file = mmtf.MMTFFile()
    mmtf_file.read(path)
    for key in mmtf_file:
        if mmtf_file.get_codec(key) is not None:
            codec = mmtf_file.get_codec(key)
            param = mmtf_file.get_param(key)
            array1 = mmtf_file[key]
            mmtf_file.set_array(key, array1, codec, param)
            array2 = mmtf_file[key]
            if array1.dtype == np.float32:
                if param != 0:
                    tol = 1/param
                else:
                    tol = 0
                assert np.isclose(array1, array2, atol=tol).all()
            else:
                assert (array1 == array2).all()


@pytest.mark.parametrize("path, single_model",
                         itertools.product(glob.glob(join(data_dir, "*.mmtf")),
                                           [False, True])
                        )
def test_array_conversion(path, single_model):
    if single_model:
        model = 1
    else:
        model = None
    mmtf_file = mmtf.MMTFFile()
    mmtf_file.read(path)
    a1 = mmtf.get_structure(mmtf_file, model=model, include_bonds=True)
    mmtf_file = mmtf.MMTFFile()
    mmtf.set_structure(mmtf_file, a1)
    a2 = mmtf.get_structure(mmtf_file, model=model, include_bonds=True)
    for category in a1.get_annotation_categories():
        assert a1.get_annotation(category).tolist() == \
               a2.get_annotation(category).tolist()
    assert a1.coord.flatten().tolist() == \
           approx(a2.coord.flatten().tolist(), abs=1e-3)


mmtf_paths = sorted(glob.glob(join(data_dir, "*.mmtf")))
cif_paths  = sorted(glob.glob(join(data_dir, "*.cif" )))
@pytest.mark.parametrize("file_index, is_stack", itertools.product(
                          [i for i in range(len(mmtf_paths))],
                          [False, True])
                        )
def test_pdbx_consistency(file_index, is_stack):
    model = None if is_stack else 1
    mmtf_file = mmtf.MMTFFile()
    mmtf_file.read(mmtf_paths[file_index])
    a1 = mmtf.get_structure(mmtf_file, model=model)
    pdbx_file = pdbx.PDBxFile()
    pdbx_file.read(cif_paths[file_index])
    a2 = pdbx.get_structure(pdbx_file, model=model)
    # Expected fail in res_id
    for category in ["chain_id", "res_name", "hetero",
                     "atom_name", "element"]:
        assert a1.get_annotation(category).tolist() == \
               a2.get_annotation(category).tolist()
    assert a1.coord.flatten().tolist() == \
           approx(a2.coord.flatten().tolist(), abs=1e-3)


def test_extra_fields():
    path = join(data_dir, "1l2y.mmtf")
    mmtf_file = mmtf.MMTFFile()
    mmtf_file.read(path)
    stack1 = mmtf.get_structure(mmtf_file, extra_fields=["atom_id","b_factor",
                                                         "occupancy","charge"])
    mmtf.set_structure(mmtf_file, stack1)
    stack2 = mmtf.get_structure(mmtf_file, extra_fields=["atom_id","b_factor",
                                                         "occupancy","charge"])
    assert stack1.atom_id.tolist() == stack2.atom_id.tolist()
    assert stack1.b_factor.tolist() == approx(stack2.b_factor.tolist())
    assert stack1.occupancy.tolist() == approx(stack2.occupancy.tolist())
    assert stack1.charge.tolist() == stack2.charge.tolist()